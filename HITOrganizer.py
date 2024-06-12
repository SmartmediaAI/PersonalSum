import os
import shutil
import json
from AssignmentFilter import AssignmentFilter


class HITOrganizer:
    def __init__(self, parsed_hits_dir, user_profiles_dir):
        self.parsed_hits_dir = parsed_hits_dir
        self.user_profiles_dir = user_profiles_dir

    def _extract_worker_id_and_assignment_id(self, file_path):
        worker_id, assignment_id = None, None
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                worker_id = data.get('WorkerId')
                assignment_id = data.get('AssignmentId')
        return worker_id, assignment_id

    def organize_file(self, assignment_id, approve=True):
        for filename in os.listdir(self.parsed_hits_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.parsed_hits_dir, filename)
                worker_id, file_assignment_id = self._extract_worker_id_and_assignment_id(
                    file_path)

                if assignment_id == file_assignment_id and worker_id is not None:
                    # Determine the target subfolder based on approval status
                    target_subfolder = 'approved' if approve else 'rejected'

                    # Create the WorkerId directory and subfolder if they don't exist
                    worker_dir_path = os.path.join(
                        self.user_profiles_dir, worker_id)
                    target_dir_path = os.path.join(
                        worker_dir_path, target_subfolder)
                    os.makedirs(target_dir_path, exist_ok=True)

                    # Copy the .json file to the target directory
                    shutil.copy(file_path, target_dir_path)
                    print(f"Copied '{filename}' to '{target_dir_path}'")

                    # Copy the corresponding .txt file to the target directory
                    txt_filename = filename.replace('.json', '.txt')
                    txt_file_path = os.path.join(
                        self.parsed_hits_dir, txt_filename)
                    if os.path.exists(txt_file_path):
                        shutil.copy(txt_file_path, target_dir_path)
                        print(
                            f"Copied '{txt_filename}' to '{target_dir_path}'")
                    return True

        print("No matching file found for the given AssignmentId.")
        return False


if __name__ == '__main__':
    # Initialize the HITOrganizer object
    # Update to your actual directory path
    parsed_hits_dir = '../ParsedNotFilteredHITS'
    user_profiles_dir = '../UserProfiles'  # Update to your actual directory path
    hit_organizer = HITOrganizer(parsed_hits_dir, user_profiles_dir)

    # Example usage
    # Replace with an actual assignment ID
    assignment_id = '3P1L2B7ADL3X983QCX1X5IHFGK7LOQ'
    # Set approve to False for rejected assignments
    # hit_organizer.organize_file(assignment_id, approve=True)

    folder_path = '../ParsedNotFilteredHITS'
    assignment_filter = AssignmentFilter(folder_path)
    filtered_assignment_ids = assignment_filter.filter_assignments()

#    for assignment_id in filtered_assignment_ids:
 #       hit_organizer.organize_file(assignment_id, approve=False)
