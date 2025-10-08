"""
Author Collaboration & Outcome Component

This component manages collaborative research activities and quarterly group decisions
of all authors in the hedge fund. Authors work primarily in small groups (1-3 people)
to either improve existing strategies or invent new ones.

This component serves as the innovation engine that drives strategy creation and
improvement, directly interfacing with the Strategy Lifecycle Component.
"""

from .author import Author, GroupActivity
from .author_collaboration_manager import AuthorCollaborationManager
from .author_factory import AuthorFactory
from .author_collaboration_parameters import AuthorCollaborationParameters

__all__ = [
    'Author',
    'GroupActivity',
    'AuthorCollaborationManager',
    'AuthorFactory',
    'AuthorCollaborationParameters'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hedgedemia Business Model Team'