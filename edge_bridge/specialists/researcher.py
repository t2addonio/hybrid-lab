from specialists.base import Specialist


class Researcher(Specialist):
    name = "researcher"
    description = "Literature, synthesis, factual grounding"

    @property
    def system_prompt(self) -> str:
        return (
            "You are the researcher specialist on Edge Bridge. "
            "Answer the task directly. Do not emit INVOKE/CONSULT/HANDOFF. "
            "Mark uncertainty. Prefer primary sources when you name them."
        )


specialist = Researcher()
