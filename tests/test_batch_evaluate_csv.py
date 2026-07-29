import json
import os
import tempfile
import unittest
from noka_eval.exporter import format_evaluations_as_csv
from noka_eval.cli import main, run_batch_evaluation


class TestBatchEvaluateCSV(unittest.TestCase):

    def test_format_evaluations_as_csv_standard(self):
        evaluations = [
            {
                "id": "eval_1",
                "student_id": "std_101",
                "score": 85.5,
                "max_score": 100,
                "status": "PASSED",
                "feedback": "Great work on the essay!",
            },
            {
                "id": "eval_2",
                "student_id": "std_102",
                "score": 52.0,
                "max_score": 100,
                "status": "NEEDS_REVIEW",
                "feedback": "Needs improvement in coherence.",
            }
        ]
        csv_out = format_evaluations_as_csv(evaluations)
        lines = csv_out.strip().split("\n")
        
        self.assertEqual(len(lines), 3)  # Header + 2 rows
        self.assertIn("id,student_id,score,max_score,status,feedback", lines[0])
        self.assertIn("eval_1,std_101,85.5,100,PASSED,Great work on the essay!", lines[1])

    def test_format_evaluations_as_csv_escaping_special_chars(self):
        evaluations = [
            {
                "id": "eval_3",
                "student_id": "std_103",
                "score": 90.0,
                "max_score": 100,
                "status": "PASSED",
                "feedback": "Excellent!\nIncludes multi-line feedback, \"quotes\", and commas.",
            }
        ]
        csv_out = format_evaluations_as_csv(evaluations)
        self.assertIn('"Excellent!\nIncludes multi-line feedback, ""quotes"", and commas."', csv_out)

    def test_format_evaluations_as_csv_empty_input(self):
        csv_out = format_evaluations_as_csv([])
        self.assertEqual(csv_out, "")

        csv_with_headers = format_evaluations_as_csv([], fieldnames=["id", "score"])
        self.assertEqual(csv_with_headers.strip(), "id,score")

    def test_cli_format_csv_file_output(self):
        sample_input = [
            {"id": "1", "student_id": "S1", "score": 95, "max_score": 100, "feedback": "Nice"},
            {"id": "2", "student_id": "S2", "score": 40, "max_score": 100, "feedback": "Redo"}
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as infile, \
             tempfile.NamedTemporaryFile(mode="r", delete=False, suffix=".csv") as outfile:
            json.dump(sample_input, infile)
            infile_path = infile.name
            outfile_path = outfile.name

        try:
            exit_code = main(["--input", infile_path, "--format", "csv", "--output", outfile_path])
            self.assertEqual(exit_code, 0)

            with open(outfile_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("id,student_id,score,max_score,status,feedback", content)
            self.assertIn("1,S1,95,100,PASSED,Nice", content)
            self.assertIn("2,S2,40,100,NEEDS_REVIEW,Redo", content)
        finally:
            if os.path.exists(infile_path):
                os.remove(infile_path)
            if os.path.exists(outfile_path):
                os.remove(outfile_path)

    def test_cli_backward_compatibility_default_format(self):
        sample_input = [{"id": "1", "student_id": "S1", "score": 80, "max_score": 100}]
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as infile, \
             tempfile.NamedTemporaryFile(mode="r", delete=False, suffix=".json") as outfile:
            json.dump(sample_input, infile)
            infile_path = infile.name
            outfile_path = outfile.name

        try:
            exit_code = main(["--input", infile_path, "--output", outfile_path])
            self.assertEqual(exit_code, 0)

            with open(outfile_path, "r", encoding="utf-8") as f:
                res = json.load(f)

            self.assertIsInstance(res, list)
            self.assertEqual(res[0]["id"], "1")
        finally:
            if os.path.exists(infile_path):
                os.remove(infile_path)
            if os.path.exists(outfile_path):
                os.remove(outfile_path)


if __name__ == "__main__":
    unittest.main()
