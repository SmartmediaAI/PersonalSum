import os
import json


class BanFilter:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def convert_to_minutes(self, duration_str):
        parts = duration_str.split(' ')  # Split '0 days' from '00:13:14'
        time_part = parts[-1]  # Get the '00:13:14' part
        # Split into hours, minutes, and seconds
        h, m, s = map(int, time_part.split(':'))
        return h * 60 + m + s / 60  # Convert to total minutes

    def filter_assignments(self):
        workerID = {}

        for file_name in os.listdir(self.folder_path):
            if file_name.endswith('.json'):
                with open(os.path.join(self.folder_path, file_name), 'r') as file:
                    data = json.load(file)

                    duration_minutes = self.convert_to_minutes(
                        data['Duration'])

                    if duration_minutes <= 5:

                        if data["WorkerId"] in workerID:
                            workerID[data["WorkerId"]] += 1

                        else:
                            workerID[data["WorkerId"]] = 1

        return workerID

    def get_worker_ids(self):

        workerIDs = []
        filtered_worker_ids = self.filter_assignments()

        for worker, job_count in filtered_worker_ids.items():
            if job_count >= 10:
                workerIDs.append(worker)

        return workerIDs


# Usage

if __name__ == '__main__':

    folder_path = '../ParsedNotFilteredHITS'
    ban_filter = BanFilter(folder_path)
    filtered_worker_ids = ban_filter.get_worker_ids()

    print(len(filtered_worker_ids))

    for worker in filtered_worker_ids:
        print(worker)
