import asyncio
import logging
import uuid
import math
import json
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Protocol, 
    TypeVar, Generic, Callable, Set, Awaitable
)
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# --- 0. INFRASTRUCTURE & LOGGING SETUP ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TITAN-KERNEL]: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TitanEngine")

# --- 1. CORE DOMAIN PRIMITIVES (The "Language" of the System) ---

T = TypeVar("T")

class Entity(ABC):
    """Base class for all persistent domain entities."""
    def __init__(self, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class ActivityType(Enum):
    # Coding
    PR_MERGE = "pr_merge"
    CODE_REVIEW = "code_review"
    BUG_FIX_CRITICAL = "bug_fix_critical"
    # Social
    MENTORSHIP_SESSION = "mentorship"
    KNOWLEDGE_SHARE = "knowledge_share"
    # Governance
    ARCH_PROPOSAL = "arch_proposal"

class CurrencyType(Enum):
    XP = "experience_points"      # For leveling
    COINS = "redeemable_coins"    # For store rewards
    KARMA = "social_reputation"   # For peer trust

@dataclass(frozen=True)
class Money:
    """Immutable Value Object for currency."""
    amount: float
    currency: CurrencyType

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, multiplier: float) -> 'Money':
        return Money(self.amount * multiplier, self.currency)

# --- 2. EVENT SOURCING LAYER (The "Truth") ---

class DomainEvent(ABC):
    """Base class for all system events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ActivitySubmittedEvent(DomainEvent):
    activity_id: str
    user_id: str
    activity_type: ActivityType
    metadata: Dict[str, Any]

@dataclass
class TransactionRecordedEvent(DomainEvent):
    transaction_id: str
    user_id: str
    debit_account: str
    credit_account: str
    amount: Money
    reason: str

@dataclass
class LevelUpEvent(DomainEvent):
    user_id: str
    old_level: int
    new_level: int
    rewards: List[Money]

class EventBus:
    """Asynchronous Pub/Sub System."""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent):
        event_type = type(event).__name__
        logger.info(f"Event Published: {event_type} -> {event}")
        if event_type in self._subscribers:
            # Run all handlers concurrently
            await asyncio.gather(*(handler(event) for handler in self._subscribers[event_type]))

# --- 3. REPOSITORY INTERFACES (The "Storage Contract") ---

class Repository(Generic[T], ABC):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]: ...
    @abstractmethod
    async def save(self, entity: T) -> None: ...

# --- 4. DOMAIN ENTITIES & LOGIC ---

@dataclass
class UserProfile(Entity):
    username: str
    level: int = 1
    # Multi-currency wallet
    wallet: Dict[CurrencyType, float] = field(default_factory=dict)
    badges: Set[str] = field(default_factory=set)
    # Anti-gaming metrics
    streak_days: int = 0
    last_activity: Optional[datetime] = None

    def deposit(self, money: Money):
        current = self.wallet.get(money.currency, 0.0)
        self.wallet[money.currency] = current + money.amount

    def calculate_level_progress(self) -> float:
        # Complex curve: XP needed = 100 * (level ^ 1.8)
        current_xp = self.wallet.get(CurrencyType.XP, 0)
        xp_next = 100 * (self.level ** 1.8)
        return current_xp / xp_next

@dataclass
class LedgerEntry(Entity):
    """Double-entry bookkeeping record."""
    debit_account: str  # e.g., 'SYSTEM_RESERVE'
    credit_account: str # e.g., 'USER_123'
    amount: float
    currency: CurrencyType
    reference_id: str   # activity_id

# --- 5. SPECIFICATION PATTERN (The "Rules Engine") ---

class RuleSpecification(ABC):
    """Base class for composable business rules."""
    @abstractmethod
    def is_satisfied_by(self, context: Dict[str, Any]) -> bool: ...

class AndSpecification(RuleSpecification):
    def __init__(self, *specs: RuleSpecification):
        self.specs = specs
    def is_satisfied_by(self, context) -> bool:
        return all(s.is_satisfied_by(context) for s in self.specs)

class HasMinCodeVolume(RuleSpecification):
    def __init__(self, min_loc: int):
        self.min_loc = min_loc
    def is_satisfied_by(self, context) -> bool:
        return context.get('lines_of_code', 0) >= self.min_loc

class IsNotLate(RuleSpecification):
    def is_satisfied_by(self, context) -> bool:
        return not context.get('is_late', False)

# --- 6. SCORING STRATEGIES (The "Brain") ---

class ScoringContext:
    def __init__(self, activity_type: ActivityType, metadata: Dict[str, Any], user: UserProfile):
        self.type = activity_type
        self.metadata = metadata
        self.user = user

class BaseScoringStrategy(ABC):
    @abstractmethod
    def calculate(self, ctx: ScoringContext) -> List[Money]: ...

class CodingStrategy(BaseScoringStrategy):
    def calculate(self, ctx: ScoringContext) -> List[Money]:
        loc = ctx.metadata.get('lines_of_code', 0)
        complexity = ctx.metadata.get('cyclomatic_complexity', 1)
        
        # 1. Base XP based on Logarithmic LOC
        xp_amount = 10 * math.log(loc + 1) * complexity
        
        # 2. Coins for bug fixes
        coins_amount = 0
        if ctx.type == ActivityType.BUG_FIX_CRITICAL:
            coins_amount = 50 * complexity

        return [
            Money(round(xp_amount, 2), CurrencyType.XP),
            Money(round(coins_amount, 2), CurrencyType.COINS)
        ]

class SocialStrategy(BaseScoringStrategy):
    def calculate(self, ctx: ScoringContext) -> List[Money]:
        attendees = ctx.metadata.get('attendee_count', 1)
        duration_hrs = ctx.metadata.get('duration_hours', 1.0)
        
        # Karma calculation
        karma_points = attendees * duration_hrs * 5
        xp_points = karma_points * 0.5

        return [
            Money(xp_points, CurrencyType.XP),
            Money(karma_points, CurrencyType.KARMA)
        ]

# --- 7. INFRASTRUCTURE IMPLEMENTATION (In-Memory Adapters) ---

class InMemoryUserRepo(Repository[UserProfile]):
    def __init__(self):
        self._store = {}
    
    async def get(self, id: str) -> Optional[UserProfile]:
        # Simulate network latency
        await asyncio.sleep(0.01)
        return self._store.get(id)
    
    async def save(self, entity: UserProfile) -> None:
        self._store[entity.id] = entity

class InMemoryLedgerRepo(Repository[LedgerEntry]):
    def __init__(self):
        self._store = []
    
    async def get(self, id: str): return None
    async def save(self, entity: LedgerEntry):
        self._store.append(entity)
        logger.debug(f"Ledger Recorded: {entity.debit_account} -> {entity.credit_account}: {entity.amount}")

# --- 8. SERVICE LAYER (The "Orchestrator") ---

class TitanService:
    def __init__(
        self, 
        user_repo: Repository[UserProfile], 
        ledger_repo: Repository[LedgerEntry],
        event_bus: EventBus
    ):
        self.user_repo = user_repo
        self.ledger_repo = ledger_repo
        self.bus = event_bus
        
        # Strategy Registry
        self.strategies = {
            ActivityType.PR_MERGE: CodingStrategy(),
            ActivityType.BUG_FIX_CRITICAL: CodingStrategy(),
            ActivityType.MENTORSHIP_SESSION: SocialStrategy(),
        }

    async def process_activity(self, user_id: str, act_type: ActivityType, metadata: Dict[str, Any]):
        """
        Main entry point. Orchestrates the entire flow transactionally.
        """
        user = await self.user_repo.get(user_id)
        if not user:
            # Auto-create for demo
            user = UserProfile(id=user_id, username=f"User_{user_id}")
        
        # 1. Publish Reception Event
        await self.bus.publish(ActivitySubmittedEvent(str(uuid.uuid4()), user_id, act_type, metadata))

        # 2. Select Strategy
        strategy = self.strategies.get(act_type)
        if not strategy:
            logger.warning(f"No strategy found for {act_type}")
            return

        # 3. Calculate Rewards
        ctx = ScoringContext(act_type, metadata, user)
        rewards = strategy.calculate(ctx)

        # 4. Apply Advanced Modifiers (Pipeline)
        # e.g., Weekend multiplier, Streak multiplier
        if self._is_weekend():
            rewards = [r * 1.1 for r in rewards] # 10% Weekend Bonus

        # 5. Execute Transaction (Double Entry Ledger)
        for reward in rewards:
            if reward.amount <= 0: continue
            
            # Create Ledger Entry
            ledger_entry = LedgerEntry(
                debit_account="SYSTEM_MINT",
                credit_account=user.id,
                amount=reward.amount,
                currency=reward.currency,
                reference_id=f"ACT-{datetime.now().timestamp()}"
            )
            await self.ledger_repo.save(ledger_entry)
            
            # Update User State
            user.deposit(reward)
            
            # Publish Financial Event
            await self.bus.publish(TransactionRecordedEvent(
                ledger_entry.id, user.id, "SYSTEM_MINT", user.id, reward, "Activity Reward"
            ))

        # 6. Check Level Up Logic
        await self._check_level_up(user)
        
        # 7. Persist User
        await self.user_repo.save(user)

    async def _check_level_up(self, user: UserProfile):
        required_xp = 100 * (user.level ** 1.8)
        current_xp = user.wallet.get(CurrencyType.XP, 0)
        
        if current_xp >= required_xp:
            old_level = user.level
            user.level += 1
            # Level up bonus
            bonus = Money(500, CurrencyType.COINS)
            user.deposit(bonus)
            
            logger.info(f"🚀 LEVEL UP! {user.username} is now Level {user.level}")
            await self.bus.publish(LevelUpEvent(user.id, old_level, user.level, [bonus]))

    def _is_weekend(self) -> bool:
        return datetime.today().weekday() >= 5

# --- 9. GAMIFICATION HANDLERS (The "Fun" Part) ---

class GamificationEngine:
    def __init__(self, service: TitanService):
        self.service = service
        # Wire up event listeners
        self.service.bus.subscribe("TransactionRecordedEvent", self.on_transaction)
        self.service.bus.subscribe("LevelUpEvent", self.on_level_up)

    async def on_transaction(self, event: DomainEvent):
        if isinstance(event, TransactionRecordedEvent):
            # Example: Check for "Richie Rich" Badge
            if event.amount.currency == CurrencyType.COINS and event.amount.amount > 100:
                logger.info(f"🏅 BADGE EARNED: 'Big Earner' for User {event.user_id}")

    async def on_level_up(self, event: DomainEvent):
        # Trigger global announcement logic here
        pass

# --- 10. SIMULATION RUNNER ---

async def main():
    print("Initializing TITAN ENGINE...")
    
    # 1. Setup DI
    event_bus = EventBus()
    user_repo = InMemoryUserRepo()
    ledger_repo = InMemoryLedgerRepo()
    
    titan = TitanService(user_repo, ledger_repo, event_bus)
    gamification = GamificationEngine(titan) # Hooks up listeners
    
    # 2. Simulate User Activity Stream
    user_id = "u_dev_007"
    
    print("\n--- Event 1: Simple PR Merge ---")
    await titan.process_activity(
        user_id, 
        ActivityType.PR_MERGE, 
        {"lines_of_code": 120, "cyclomatic_complexity": 1.5}
    )

    print("\n--- Event 2: Critical Bug Fix (High Value) ---")
    await titan.process_activity(
        user_id, 
        ActivityType.BUG_FIX_CRITICAL, 
        {"lines_of_code": 50, "cyclomatic_complexity": 5.0} # High complexity
    )

    print("\n--- Event 3: Hosting a Workshop (Social) ---")
    await titan.process_activity(
        user_id, 
        ActivityType.MENTORSHIP_SESSION, 
        {"attendee_count": 20, "duration_hours": 2.0}
    )
    
    # 3. Inspect Final State
    user = await user_repo.get(user_id)
    print(f"\n--- FINAL USER STATE [{user.username}] ---")
    print(f"Level: {user.level}")
    print(f"Wallet: {json.dumps({k.name: round(v, 2) for k, v in user.wallet.items()}, indent=2)}")
    print(f"Badges: {user.badges}")

if __name__ == "__main__":
    asyncio.run(main())