class BandEstimator:
    def __init__(self, mode="ielts"):
        self.mode = mode.lower()
        if self.mode not in ["ielts", "toefl"]:
            raise ValueError("Mode must be 'ielts' or 'toefl'")

    def estimate(self, text):
        length = len(text.split())
        if self.mode == "ielts":
            return self._estimate_ielts(length)
        else:
            return self._estimate_toefl(length)

    def _estimate_ielts(self, length):
        if length > 250:
            return 7.5
        elif length > 150:
            return 6.0
        return 5.0

    def _estimate_toefl(self, length):
        if length > 300:
            return 28
        elif length > 200:
            return 22
        return 15

if __name__ == "__main__":
    estimator = BandEstimator("ielts")
    score = estimator.estimate("This is a dummy essay that is very short.")
    print(f"IELTS Score: {score}")