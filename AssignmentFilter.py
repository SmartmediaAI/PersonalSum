import os
import json
from langdetect import detect
from langdetect import DetectorFactory
DetectorFactory.seed = 0


class AssignmentFilter:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def convert_to_minutes(self, duration_str):
        parts = duration_str.split(' ')  # Split '0 days' from '00:13:14'
        time_part = parts[-1]  # Get the '00:13:14' part
        # Split into hours, minutes, and seconds
        h, m, s = map(int, time_part.split(':'))
        return h * 60 + m + s / 60  # Convert to total minutes

    def check_answers(self, questions_and_answers):
        correct_count = 3

        for qa in questions_and_answers[3:]:
            answer = qa["Answers"][0]["Answer"].split("_")[0]
            # Check if there are answers and the first one is correct
            if answer == "incorrect":
                correct_count -= 1
        # Return True if there are less than two correct answers
        return correct_count < 2

    def check_source_in_summary(self, questions_and_answers):
        source_is_insuficient = False
        for qa in questions_and_answers[3:]:

            summary = qa["Answers"][1]['Answer']
            source = qa["Answers"][2]['Answer']

            if source in summary:
                source_is_insuficient = True

        return source_is_insuficient

    def check_source_in_text(self, questions_and_answers):

        source_in_text = True

        for qa in questions_and_answers[3:]:

            article = qa["QuestionText"]
            source = qa["Answers"][2]['Answer']

            source_elements = source.split(".")

            num_elements_in_article = 0

            for element in source_elements:
                if element in article:
                    num_elements_in_article += 1

            avg_elements_in_article = num_elements_in_article / \
                len(source_elements)

            if avg_elements_in_article < 0.95:
                source_in_text = False

        return source_in_text

    def check_summary_in_text(self, questions_and_answers):

        summary_in_text = False

        for qa in questions_and_answers[3:]:

            questionText = qa["QuestionText"]
            summary = qa["Answers"][1]['Answer']

            if summary in questionText:
                summary_in_text = True

        return summary_in_text

    def checkLenghtOfSummary(self, questions_and_answers):
        summary_is_too_short = False
        for qa in questions_and_answers[3:]:

            summary = qa["Answers"][1]['Answer']
            if len(summary) < 20:
                summary_is_too_short = True

        return summary_is_too_short

    def checkLengthOfSource(self, questions_and_answers):
        source_is_too_short = False
        for qa in questions_and_answers[3:]:

            source = qa["Answers"][2]['Answer']
            if len(source) < 15:
                source_is_too_short = True

        return source_is_too_short

    def checkLanguage(self, questions_and_answers, assignmentID):
        summary_or_source_is_not_norwegian = False

        for qa in questions_and_answers[3:]:
            summary = qa["Answers"][1]['Answer']
            source = qa["Answers"][2]['Answer']

            # Function to check if text is suitable for language detection
            def is_suitable_for_detection(text, min_length):
                # Ensure the text is not empty, meets minimum length, and contains alphabetic characters
                return len(text) >= min_length and any(char.isalpha() for char in text)

            try:
                # Check for summary with minimum 20 characters
                if is_suitable_for_detection(summary, 20):
                    summary_language = detect(summary)
                    if summary_language != 'no':
                        summary_or_source_is_not_norwegian = True

                # Check for source with minimum 15 characters
                if is_suitable_for_detection(source, 15):
                    source_language = detect(source)
                    if source_language != 'no':
                        summary_or_source_is_not_norwegian = True
            except Exception as e:
                # If exception occurs, the reason is most likely beacuse they have passed a link as source
                summary_or_source_is_not_norwegian = True

        return summary_or_source_is_not_norwegian

    def filter_assignments(self):
        assignment_ids = []

        for file_name in os.listdir(self.folder_path):
            if file_name.endswith('.json'):
                with open(os.path.join(self.folder_path, file_name), 'r') as file:
                    data = json.load(file)

                    duration_minutes = self.convert_to_minutes(
                        data['Duration'])

                    are_answers_insufficient = self.check_answers(
                        data['QuestionsAndAnswers'])

                    are_source_in_summary = self.check_source_in_summary(
                        data['QuestionsAndAnswers'])

                    are_source_in_text = self.check_source_in_text(
                        data['QuestionsAndAnswers'])

                    are_summary_too_short = self.checkLenghtOfSummary(
                        data['QuestionsAndAnswers'])

                    are_source_too_short = self.checkLengthOfSource(
                        data['QuestionsAndAnswers'])

                    are_language_not_norwegian = self.checkLanguage(
                        data['QuestionsAndAnswers'], data['AssignmentId'])

                    are_summary_in_text = self.check_summary_in_text(
                        data['QuestionsAndAnswers'])

                    if duration_minutes < 5 or are_answers_insufficient or are_source_in_summary or are_summary_too_short or are_summary_in_text or are_source_too_short or are_language_not_norwegian or not are_source_in_text:
                        assignment_ids.append(data['AssignmentId'])

        print("DONE")
        return assignment_ids


# Usage

"""
folder_path = 'ParsedNotFilteredHITS'
assignment_filter = AssignmentFilter(folder_path)
filtered_assignment_ids = assignment_filter.filter_assignments()
print(len(filtered_assignment_ids))

for assignment_id in filtered_assignment_ids:
    print(assignment_id)
"""
