"""
Author and GroupActivity data structures for Author Collaboration & Outcome Component.

This module defines the core data structures for tracking authors and their
collaborative activities within the hedge fund simulation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid


@dataclass
class Author:
    """
    Represents an author (researcher/trader) in the hedge fund.

    Authors work in collaborative groups to invent new strategies or improve
    existing ones. Each author has a finite research period (2-4 quarters)
    during which they can participate in activities.
    """

    # Identity
    author_id: str
    name: str
    hire_quarter: int

    # Research cycle tracking
    remaining_research_quarters: int
    current_activity_state: str = 'available'  # 'available' | 'inventing_quarter_1'
    invention_group_id: Optional[str] = None
    total_research_quarters_spent: int = 0

    # Decision probabilities (assigned at hiring, remain constant)
    invention_probability: float = 0.0
    improvement_probability: float = 0.0

    # Contribution tracking (for Performance Allocation Component)
    strategies_created: List[str] = field(default_factory=list)  # strategy_ids
    strategies_improved: List[str] = field(default_factory=list)  # strategy_ids
    lifetime_success_count: int = 0
    quarterly_contributions: List[Dict[str, Any]] = field(default_factory=list)

    # Group participation history
    group_participation_history: List[Dict[str, Any]] = field(default_factory=list)

    # Safety net and payment tracking (for Performance Allocation Component)
    safety_net_enrolled: bool = False
    safety_net_enrollment_quarter: Optional[int] = None
    performance_payments: Dict[int, float] = field(default_factory=dict)  # quarter -> amount
    safety_net_payments: Dict[int, float] = field(default_factory=dict)   # quarter -> amount

    # Status
    is_active: bool = True
    departure_quarter: Optional[int] = None
    departure_reason: Optional[str] = None  # 'retirement', 'performance', 'voluntary'

    def __post_init__(self):
        """Initialize derived fields after object creation."""
        if not self.author_id:
            self.author_id = f"author_{str(uuid.uuid4())[:8]}"

    def enroll_in_safety_net(self, quarter: int) -> None:
        """
        Enroll in safety net program when contributing to any strategy.

        Args:
            quarter: Quarter when enrollment occurs
        """
        if not self.safety_net_enrolled:
            self.safety_net_enrolled = True
            self.safety_net_enrollment_quarter = quarter

    def record_performance_payment(self, amount: float, quarter: int) -> None:
        """
        Record a performance allocation payment for history tracking.

        Args:
            amount: Payment amount in millions
            quarter: Quarter when payment received
        """
        self.performance_payments[quarter] = amount

    def record_safety_net_payment(self, amount: float, quarter: int) -> None:
        """
        Record a safety net payment for history tracking.

        Args:
            amount: Payment amount in millions
            quarter: Quarter when payment received
        """
        self.safety_net_payments[quarter] = amount

    def get_lifetime_payments(self) -> float:
        """
        Get total lifetime payments for safety net eligibility check.

        Returns:
            float: Total lifetime payments (performance + safety net)
        """
        return sum(self.performance_payments.values()) + sum(self.safety_net_payments.values())

    def get_quarterly_payment_history(self) -> Dict[int, Dict[str, float]]:
        """
        Get complete quarterly payment history.

        Returns:
            Dict mapping quarter to payment breakdown
        """
        all_quarters = set(self.performance_payments.keys()) | set(self.safety_net_payments.keys())
        history = {}

        for quarter in sorted(all_quarters):
            history[quarter] = {
                'performance': self.performance_payments.get(quarter, 0.0),
                'safety_net': self.safety_net_payments.get(quarter, 0.0),
                'total': self.performance_payments.get(quarter, 0.0) + self.safety_net_payments.get(quarter, 0.0)
            }

        return history

    def advance_quarter(self) -> None:
        """
        Advance the author by one quarter.
        Decrements remaining research time and updates total time spent.
        """
        if self.remaining_research_quarters > 0:
            self.remaining_research_quarters -= 1
            self.total_research_quarters_spent += 1

        # Check for retirement
        if self.remaining_research_quarters == 0 and self.is_active:
            self.retire()

    def retire(self) -> None:
        """Mark author as retired when research time expires."""
        self.is_active = False
        self.departure_quarter = self.total_research_quarters_spent + self.hire_quarter
        self.departure_reason = 'retirement'
        self.current_activity_state = 'retired'

    def is_available_for_activity(self) -> bool:
        """Check if author can participate in new activities this quarter."""
        return (self.is_active and
                self.remaining_research_quarters > 0 and
                self.current_activity_state == 'available')

    def can_attempt_invention(self) -> bool:
        """Check if author has enough time remaining for 2-quarter invention process."""
        return (self.is_available_for_activity() and
                self.remaining_research_quarters >= 2)

    def start_invention_process(self, group_id: str) -> None:
        """Mark author as starting invention (quarter 1 of 2)."""
        if not self.can_attempt_invention():
            raise ValueError(f"Author {self.author_id} cannot start invention process")

        self.current_activity_state = 'inventing_quarter_1'
        self.invention_group_id = group_id

    def complete_invention_process(self) -> None:
        """Complete invention process and return to available state."""
        self.current_activity_state = 'available'
        self.invention_group_id = None

    def record_successful_contribution(self, activity_type: str, strategy_id: str,
                                     quarter: int, group_members: List[str]) -> None:
        """Record a successful contribution for tracking and performance allocation."""
        self.lifetime_success_count += 1

        if activity_type == 'invention':
            self.strategies_created.append(strategy_id)
        elif activity_type in ['improve_return', 'improve_capacity']:
            if strategy_id not in self.strategies_improved:
                self.strategies_improved.append(strategy_id)

        # Record detailed contribution
        contribution_record = {
            'quarter': quarter,
            'activity_type': activity_type,
            'strategy_id': strategy_id,
            'success': True,
            'group_members': group_members.copy(),
            'group_size': len(group_members)
        }
        self.quarterly_contributions.append(contribution_record)

        # Record group participation
        group_record = {
            'quarter': quarter,
            'activity_type': activity_type,
            'group_members': group_members.copy(),
            'success': True
        }
        self.group_participation_history.append(group_record)

    def record_failed_contribution(self, activity_type: str, quarter: int,
                                 group_members: List[str]) -> None:
        """Record a failed contribution attempt for tracking."""
        contribution_record = {
            'quarter': quarter,
            'activity_type': activity_type,
            'strategy_id': None,
            'success': False,
            'group_members': group_members.copy(),
            'group_size': len(group_members)
        }
        self.quarterly_contributions.append(contribution_record)

        # Record group participation (even if failed)
        group_record = {
            'quarter': quarter,
            'activity_type': activity_type,
            'group_members': group_members.copy(),
            'success': False
        }
        self.group_participation_history.append(group_record)

    def get_contribution_summary(self) -> Dict[str, Any]:
        """Get summary of author's contributions for Performance Allocation Component."""
        return {
            'author_id': self.author_id,
            'strategies_created': self.strategies_created.copy(),
            'strategies_improved': self.strategies_improved.copy(),
            'lifetime_success_count': self.lifetime_success_count,
            'is_active': self.is_active,
            'departure_quarter': self.departure_quarter,
            'quarterly_contributions': self.quarterly_contributions.copy()
        }


@dataclass
class GroupActivity:
    """
    Represents a collaborative activity undertaken by a group of authors.

    Tracks the outcome and details of group activities like strategy invention
    or improvement attempts.
    """

    # Group composition
    group_members: List[str]  # List of author_ids
    group_id: str

    # Activity details
    activity_type: str  # 'improvement', 'invention_start', 'invention_complete'
    quarter: int

    # Outcome
    success: Optional[bool] = None  # None for invention_start (pending)

    # Activity-specific details
    target_strategy_id: Optional[str] = None  # For improvements
    created_strategy_id: Optional[str] = None  # For successful inventions
    improvement_type: Optional[str] = None  # 'return' or 'capacity' for improvements

    # Group dynamics
    group_success_probability: float = 0.0
    individual_probabilities: List[float] = field(default_factory=list)

    def __post_init__(self):
        """Initialize derived fields after object creation."""
        if not self.group_id:
            self.group_id = f"group_{self.quarter}_{str(uuid.uuid4())[:8]}"

    def calculate_group_success_probability(self, author_probabilities: List[float]) -> float:
        """Calculate group success probability as average of member probabilities."""
        if not author_probabilities:
            return 0.0

        self.individual_probabilities = author_probabilities.copy()
        self.group_success_probability = sum(author_probabilities) / len(author_probabilities)
        return self.group_success_probability

    def is_invention_activity(self) -> bool:
        """Check if this is an invention-related activity."""
        return self.activity_type in ['invention_start', 'invention_complete']

    def is_improvement_activity(self) -> bool:
        """Check if this is an improvement activity."""
        return self.activity_type == 'improvement'

    def is_pending(self) -> bool:
        """Check if activity is still pending completion."""
        return self.success is None

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of group activity for reporting and analysis."""
        return {
            'group_id': self.group_id,
            'activity_type': self.activity_type,
            'quarter': self.quarter,
            'group_size': len(self.group_members),
            'group_members': self.group_members.copy(),
            'success': self.success,
            'group_success_probability': self.group_success_probability,
            'target_strategy_id': self.target_strategy_id,
            'created_strategy_id': self.created_strategy_id,
            'improvement_type': self.improvement_type
        }