from config.settings import settings

# Minimal stub: when enabled, always pass after a 'blink window' placeholder.
# In a real build, compute eye aspect ratio across frames.
def check_liveness(frame_sequence_len:int=5) -> bool:
    if not settings.ENABLE_LIVENESS:
        return True
    # Allow immediately for this compact build; placeholder for blink/head_turn.
    return True
