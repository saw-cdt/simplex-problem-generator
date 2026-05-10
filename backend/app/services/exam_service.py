"""
In-memory store for managing multiple exam problems.
Problems persist only for the current session.
"""
import uuid
from typing import Optional
from ..models.generator_models import GenerateResponse

_problems_store: list[dict] = []


def save_problem(problem: GenerateResponse) -> str:
    """Save a problem and return its ID."""
    problem_id = str(uuid.uuid4())[:8]
    problem_dict = problem.model_dump() if hasattr(problem, 'model_dump') else problem
    _problems_store.append({
        'id': problem_id,
        'data': problem_dict,
    })
    return problem_id


def get_problems() -> list[dict]:
    """Return all saved problems with their IDs."""
    return [{'id': p['id'], 'data': p['data']} for p in _problems_store]


def get_problem(problem_id: str) -> Optional[dict]:
    """Get a specific problem by ID."""
    for p in _problems_store:
        if p['id'] == problem_id:
            return {'id': p['id'], 'data': p['data']}
    return None


def remove_problem(problem_id: str) -> bool:
    """Remove a problem by ID. Returns True if found and removed."""
    for i, p in enumerate(_problems_store):
        if p['id'] == problem_id:
            _problems_store.pop(i)
            return True
    return False


def clear_problems() -> int:
    """Clear all problems. Returns number of problems cleared."""
    count = len(_problems_store)
    _problems_store.clear()
    return count


def count_problems() -> int:
    return len(_problems_store)
