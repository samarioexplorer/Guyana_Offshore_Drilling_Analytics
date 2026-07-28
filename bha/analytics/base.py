from dataclasses import dataclass


@dataclass(slots=True)
class BaseAnalytics:

    module_name: str = ""

    @property
    def summary(self):
        return {}

    @property
    def score(self):
        return None

    @property
    def recommendations(self):
        return []

    def as_dict(self):

        return self.summary

    def __repr__(self):

        return (
            f"{self.module_name}"
            f"({self.summary})"
        )