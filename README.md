# PersonalSum

PersonalSum: A User-Subjective Guided Personalized Summarization Dataset for Large Language Models

## Overview

This repository contains the code and data for the research project "PersonalSum: A User-Subjective Guided Personalized Summarization Dataset for Large Language Models." This project aims to create a high-quality, personalized summarization dataset and investigate the differences between generic machine-generated summaries and those personalized to individual users' preferences.

## Repository Structure

The repository is structured as follows:

```
.
├── AssignmentFilter.py
├── BanFilter.py
├── HITOrganizer.py
├── README.md
├── dataset
│   ├── PersonalSum_original.csv
│   └── Topic_centric_PersonalSum.csv
├── main.ipynb
├── mturk_helpers.py
├── old_main_with_definitions.ipynb
└── requirements.txt
```

### Files and Directories

- `AssignmentFilter.py`: Contains the `AssignmentFilter` class used to filter assignments based on various quality metrics.
- `BanFilter.py`: Contains the `BanFilter` class used to identify workers who consistently submit low-quality work.
- `HITOrganizer.py`: Contains the `HITOrganizer` class used to organize HIT (Human Intelligence Task) files and move them based on approval status.
- `main.ipynb`: A Jupyter Notebook that ties together the functionalities of other scripts to filter, approve, reject, and organize assignments in an interactive format.
- `mturk_helpers.py`: Contains helper functions used to manage MTurk HITs, such as creating HITs, processing directories, and handling qualifications.
- `old_main_with_definitions.ipynb`: An older version of the main notebook with all function definitions included.
- `README.md`: This file.
- `dataset/`: Directory containing the original and topic-centric datasets.
  - `PersonalSum_original.csv`: The original dataset.
  - `Topic_centric_PersonalSum.csv`: The topic-centric dataset.
- `requirements.txt`: Lists the dependencies required to run the project.

## Setup and Installation

To run the project, you need to have Python installed on your system. It's recommended to use a virtual environment to manage dependencies.

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/PersonalSum.git
   cd PersonalSum
   ```

2. **Create a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Filtering Assignments

To filter assignments based on various quality metrics, use the `AssignmentFilter` class. This class checks for several criteria such as duration of task, language used, and quality of summaries.

Example usage:

```python
from AssignmentFilter import AssignmentFilter

folder_path = 'path/to/your/data'
assignment_filter = AssignmentFilter(folder_path)
filtered_assignment_ids = assignment_filter.filter_assignments()

print(f"Filtered {len(filtered_assignment_ids)} assignments:")
for assignment_id in filtered_assignment_ids:
    print(assignment_id)
```

### Banning Workers

To identify and ban workers who consistently submit low-quality work, use the `BanFilter` class.

Example usage:

```python
from BanFilter import BanFilter

folder_path = 'path/to/your/data'
ban_filter = BanFilter(folder_path)
filtered_worker_ids = ban_filter.get_worker_ids()

print(f"Banned {len(filtered_worker_ids)} workers:")
for worker_id in filtered_worker_ids:
    print(worker_id)
```

### Organizing HIT Files

To organize HIT files based on approval status, use the `HITOrganizer` class.

Example usage:

```python
from HITOrganizer import HITOrganizer

parsed_hits_dir = 'path/to/parsed/hits'
user_profiles_dir = 'path/to/user/profiles'
hit_organizer = HITOrganizer(parsed_hits_dir, user_profiles_dir)

# Organize a specific assignment
assignment_id = 'your_assignment_id'
hit_organizer.organize_file(assignment_id, approve=True)
```

### MTurk Helpers

The `mturk_helpers.py` file contains various functions to handle MTurk HITs. Import the required functions in your script or notebook as needed.

Example usage:

```python
from mturk_helpers import *

# Initialize MTurk client
load_dotenv()  # This loads the environment variables from .env
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-1'
endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

mturk = boto3.client(
    'mturk',
    endpoint_url=endpoint_url,
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

# Print account balance
print(mturk.get_account_balance()['AvailableBalance'])

# Example to process directory in chunks
input_directory = 'path/to/your/input_directory'
output_directory = 'path/to/your/output_directory'
process_directory_in_chunks(input_directory, output_directory)
```

### Jupyter Notebook

The `main.ipynb` provides the same functionalities as the scripts but in an interactive Jupyter Notebook format. You can run and modify the notebook cells to process the assignments step by step.

To open the notebook, run:

```sh
jupyter notebook main.ipynb
```

## Datasets

The `dataset` directory contains two CSV files:

- `PersonalSum_original.csv`: The original dataset with personalized summaries.
- `Topic_centric_PersonalSum.csv`: The dataset organized around specific topics.

## License

This project is licensed under the [LICENCE]. See the `LICENSE` file for more details.

## Contact

For any questions or issues, please contact [your_email@example.com].
