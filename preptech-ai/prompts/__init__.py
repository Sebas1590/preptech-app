"""Biblioteca de prompts de Coach PrepTech.

Todos los prompts internos viven aquí; app.py y services/ solo los importan.
"""
from .algorithms import ALGORITHMS_MODE
from .behavioral import BEHAVIORAL_MODE
from .feedback import FEEDBACK_FORMAT
from .few_shot import FEW_SHOT_EXAMPLES, FEW_SHOT_INSTRUCTION, build_few_shot_messages
from .one_shot import ONE_SHOT_EXAMPLE, ONE_SHOT_INSTRUCTION, build_one_shot_messages
from .system import SYSTEM_PROMPT, build_system_prompt
from .system_design import SYSTEM_DESIGN_MODE
from .zero_shot import ZERO_SHOT_PROMPT, build_zero_shot_messages

TECHNIQUES = {
    "Zero-shot": build_zero_shot_messages,
    "One-shot": build_one_shot_messages,
    "Few-shot": build_few_shot_messages,
}

__all__ = [
    "ALGORITHMS_MODE", "BEHAVIORAL_MODE", "SYSTEM_DESIGN_MODE", "FEEDBACK_FORMAT",
    "SYSTEM_PROMPT", "build_system_prompt", "ZERO_SHOT_PROMPT", "ONE_SHOT_INSTRUCTION",
    "ONE_SHOT_EXAMPLE", "FEW_SHOT_INSTRUCTION", "FEW_SHOT_EXAMPLES", "TECHNIQUES",
    "build_zero_shot_messages", "build_one_shot_messages", "build_few_shot_messages",
]
