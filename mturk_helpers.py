import boto3
import os
import xmltodict
import chardet
import re
import xml.etree.ElementTree as ET
import json
import datetime
import concurrent.futures
import threading
import pandas as pd
from datetime import timezone, timedelta
import pytz  # For timezone operations


def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


def extract_body_from_text(file_path):
    with open(file_path, "rb") as file:
        raw_data = file.read()
    try:
        content = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        print(f"Unicode Decode Error in file: {file_path}. Skipping file.")
        return None

    if "Body:" in content and "Category:" in content:
        body = content.split("Body:")[1].split("Category:")[0].strip()
        body = remove_emojis(body)
        return body
    else:
        print(f"Markers not found in file: {file_path}")
        return None


def extract_qa_pairs(content):
    qa_pairs = []
    true_qa_section = content.split("True QA:")[1].split("False QA:")[0].strip()
    false_qa_sections = content.split("False QA:")[1:]

    true_qa_parts = [
        part
        for part in true_qa_section.split("\n")
        if part.startswith("Question") or part.startswith("Answer")
    ]
    for i in range(0, len(true_qa_parts), 2):
        if i + 1 < len(true_qa_parts):
            question = true_qa_parts[i].split("Question")[1].strip()
            answer = true_qa_parts[i + 1].split("Answer")[1].strip()
            qa_pairs.append((question, answer, True))

    for section in false_qa_sections:
        parts = [
            part
            for part in section.split("\n")
            if part.startswith("Question") or part.startswith("Answer")
        ]
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                question = parts[i].split("Question")[1].strip()
                answer = parts[i + 1].split("Answer")[1].strip()
                qa_pairs.append((question, answer, False))

    return qa_pairs


def parse_question_xml(question_xml):
    question_data = xmltodict.parse(question_xml)
    questions = question_data["QuestionForm"]["Overview"]
    parsed_questions = []
    for question in questions:
        title = question.get("Title", "No Title")
        text = question["Text"]
        parsed_questions.append({"Title": title, "Text": text})
    return parsed_questions


def parse_answer_xml(answer_xml):
    parsed_data = xmltodict.parse(answer_xml)
    parsed_answers = []
    passed = 3

    if (
        "QuestionFormAnswers" in parsed_data
        and "Answer" in parsed_data["QuestionFormAnswers"]
    ):
        answers = parsed_data["QuestionFormAnswers"]["Answer"]
        if not isinstance(answers, list):
            answers = [answers]

        for answer in answers:
            qid = answer["QuestionIdentifier"]
            answer_text = answer.get(
                "FreeText", answer.get("SelectionIdentifier", "No Answer Text")
            )
            if "incorrect" in answer_text:
                passed -= 1
            parsed_answers.append({"Question ID": qid, "Answer": answer_text})

    return parsed_answers, passed


def create_HIT_test_xml(files, questions_per_text=3):
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append(
        '<QuestionForm xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd">'
    )
    xml_parts.append(
        "<Overview><Text>Velkommen til oppgaven! Vennligst les teksten nedenfor nøye. Din oppgave er å velge det korrekte spørsmål-svar paret som tilsvarer teksten og gi en oppsummering på to til tre setninger av den delen i teksten du syntes var mest interessant. Oppsumeringen skal ikke være på jeg form, og ikke inneholde annen tekst enn bare oppsummeringen. I kilder feltet skal du kopiere inn den delen av nyhetsartikkelen du oppsumerte, har du eksempelvis oppsumert fra de første tre setningene i nyhetsartikkelen skal du kopiere inn disse. Her er det viktig at du ikke skriver inn setninger som ikke finnes i den originale teksten.</Text></Overview>"
    )
    xml_parts.append(
        "<Overview><Text>Teksten din vil bli evaluert basert på nøyaktigheten av svarene dine. For å unngå avvisning, er det viktig at du svarer korrekt på kontrollspørsmålene og velger et spørsmål-svar par som nøyaktig reflekterer informasjonen i teksten. Ukorrekte eller irrelevante svar kan føre til at bidraget ditt blir avvist.</Text></Overview>"
    )
    xml_parts.append(
        "<Overview><Text>Du kan kvalifisere deg for en bonus basert på kvaliteten og kvantiteten av arbeidet ditt. Høykvalitetsbidrag som viser en grundig forståelse av teksten og et presist valg av spørsmål-svar par, vil øke sjansene dine for å motta en bonus. Jo flere oppgaver du fullfører med høy kvalitet, desto større er sjansen for bonus.</Text></Overview>"
    )

    for idx, file_path in enumerate(files, start=1):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        body = extract_body_from_text(file_path)
        if not body:
            continue

        qa_pairs = extract_qa_pairs(content)
        xml_parts.append(
            f"<Overview><Title>Tekst {idx}</Title><Text><![CDATA[{body}]]></Text></Overview>"
        )

        question_element = f"<Question><QuestionIdentifier>text{idx}_questions</QuestionIdentifier><IsRequired>true</IsRequired>"
        question_element += "<QuestionContent><Text>Velg korrekt spørsmål-svar par som tilhører teksten:</Text></QuestionContent>"
        selections = ""
        for q_idx, (question, answer, is_correct) in enumerate(
            qa_pairs[:questions_per_text], start=1
        ):
            selection_id = f'{"correct" if is_correct else "incorrect"}_{idx}_{q_idx}'
            selection = f"<Selection><SelectionIdentifier>{selection_id}</SelectionIdentifier><Text><![CDATA[Spørsmål {question} Svar {answer}]]></Text></Selection>"
            selections += selection

        question_element += f"<AnswerSpecification><SelectionAnswer><StyleSuggestion>radiobutton</StyleSuggestion><Selections>{selections}</Selections></SelectionAnswer></AnswerSpecification></Question>"
        xml_parts.append(question_element)

        summary_question = f"<Question><QuestionIdentifier>text{idx}_summary</QuestionIdentifier><IsRequired>true</IsRequired>"
        summary_question += "<QuestionContent><Text>Skriv en oppsummering på to til tre setninger av den delen i teksten du syntes var mest interessant. Oppsumeringen skal ikke være på jeg form:</Text></QuestionContent>"
        summary_question += '<AnswerSpecification><FreeTextAnswer><Constraints><Length minLength="1" /></Constraints></FreeTextAnswer></AnswerSpecification></Question>'

        xml_parts.append(summary_question)

        source_question = f"<Question><QuestionIdentifier>text{idx}_source</QuestionIdentifier><IsRequired>true</IsRequired>"
        source_question += "<QuestionContent><Text>Kilde - Kopier inn den delen av nyhetsartikkelen du oppsumerte fra:</Text></QuestionContent>"
        source_question += '<AnswerSpecification><FreeTextAnswer><Constraints><Length minLength="1" /></Constraints></FreeTextAnswer></AnswerSpecification></Question>'
        xml_parts.append(source_question)

    xml_parts.append("</QuestionForm>")
    return "".join(xml_parts)


def process_directory_in_chunks(
    directory, output_dir, chunk_size=3, questions_per_text=3
):
    os.makedirs(output_dir, exist_ok=True)
    all_filenames = [
        os.path.join(directory, f)
        for f in sorted(os.listdir(directory))
        if f.endswith(".txt")
    ]
    total_files = len(all_filenames)

    for i in range(0, total_files, chunk_size):
        chunk_files = all_filenames[i : i + chunk_size]

        if i + chunk_size >= total_files and len(chunk_files) < chunk_size:
            remaining = chunk_size - len(chunk_files)
            chunk_files.extend(all_filenames[:remaining])

        hit_xml = create_HIT_test_xml(
            chunk_files, questions_per_text=questions_per_text
        )

        output_file_path = os.path.join(output_dir, f"hit_{i // chunk_size}.xml")
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(hit_xml)
        print(f"Created HIT XML file: {output_file_path}")


def create_question_xml(field_dict, free_text_fields):
    question_form = ET.Element(
        "QuestionForm",
        xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd",
    )

    for field, options in field_dict.items():
        question = ET.SubElement(question_form, "Question")
        ET.SubElement(question, "QuestionIdentifier").text = field
        ET.SubElement(question, "IsRequired").text = "true"
        question_content = ET.SubElement(question, "QuestionContent")
        ET.SubElement(question_content, "Text").text = f"Hva er din/ditt/dine {field}?"

        if field in free_text_fields:
            answer_spec = ET.SubElement(question, "AnswerSpecification")
            free_text_answer = ET.SubElement(answer_spec, "FreeTextAnswer")
            ET.SubElement(free_text_answer, "NumberOfLinesSuggestion").text = "1"
        else:
            answer_spec = ET.SubElement(question, "AnswerSpecification")
            selection_answer = ET.SubElement(answer_spec, "SelectionAnswer")
            ET.SubElement(selection_answer, "StyleSuggestion").text = "radiobutton"
            selections = ET.SubElement(selection_answer, "Selections")

            for option in options:
                selection = ET.SubElement(selections, "Selection")
                ET.SubElement(selection, "SelectionIdentifier").text = option
                ET.SubElement(selection, "Text").text = option

    return ET.tostring(question_form, encoding="unicode")


def create_answer_key_xml(field_dict):
    answer_key = ET.Element(
        "AnswerKey",
        xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/AnswerKey.xsd",
    )
    for field in field_dict:
        question = ET.SubElement(answer_key, "Question")
        ET.SubElement(question, "QuestionIdentifier").text = field
        answer_option = ET.SubElement(question, "AnswerOption")
        ET.SubElement(answer_option, "SelectionIdentifier").text = "anyResponse"
        ET.SubElement(answer_option, "AnswerScore").text = "1"
    return ET.tostring(answer_key, encoding="unicode")


def create_qualification_type(
    mturk_client, name, description, test, answer_key, duration
):
    response = mturk_client.create_qualification_type(
        Name=name,
        Description=description,
        Test=test,
        AnswerKey=answer_key,
        TestDurationInSeconds=duration,
        QualificationTypeStatus="Active",
        AutoGranted=False,
    )
    return response["QualificationType"]["QualificationTypeId"]


def list_my_qualifications(mturk_client):
    my_qualifications = []
    next_token = None
    while True:
        if next_token:
            response = mturk_client.list_qualification_types(
                MustBeRequestable=True,
                MustBeOwnedByCaller=True,
                MaxResults=100,
                NextToken=next_token,
            )
        else:
            response = mturk_client.list_qualification_types(
                MustBeRequestable=True, MustBeOwnedByCaller=True, MaxResults=100
            )

        my_qualifications.extend(response["QualificationTypes"])
        next_token = response.get("NextToken")
        if not next_token:
            break
    return my_qualifications


def create_hit_with_xml_file(xml_file_path, mturk_client, qualification_type_id):
    with open(xml_file_path, "r") as file:
        question_xml = file.read()
    response = mturk_client.create_hit(
        Title="NorwAI Norwegian/Norsk Annotation",
        Description="Les en nyhetsartikkel og gi et sammendrag og svar på spørsmål.",
        Keywords="nyheter, annotering, sammendrag, lesing",
        Reward="6.00",
        MaxAssignments=2,
        LifetimeInSeconds=1920000,
        AssignmentDurationInSeconds=1800,
        Question=question_xml,
        QualificationRequirements=[
            {
                "QualificationTypeId": qualification_type_id,
                "Comparator": "Exists",
                "ActionsGuarded": "Accept",
            },
            {
                "QualificationTypeId": "000000000000000000L0",
                "Comparator": "GreaterThan",
                "IntegerValues": [60],
                "ActionsGuarded": "Accept",
            },
        ],
    )
    return response["HIT"]["HITId"]


def check_qualification(answers):
    for answer in answers:
        if (
            answer["Question ID"] == "Norsk språkferdigheter"
            and answer["Answer"] != "Flytende"
        ):
            return False
    return True


def approve_qualifications(mturk_client, qualification_type_id, file_name):
    try:
        qualification_requests = mturk_client.list_qualification_requests(
            QualificationTypeId=qualification_type_id, MaxResults=100
        )
        for request in qualification_requests.get("QualificationRequests", []):
            request_id = request["QualificationRequestId"]
            if not check_qualification(parse_answer_xml(request["Answer"])[0]):
                print(
                    f"Qualification request {request_id} did not meet the criteria. Rejecting..."
                )
                mturk_client.reject_qualification_request(
                    QualificationRequestId=request_id,
                    Reason="Your answers did not meet the criteria for this qualification.",
                )
                continue
            request_json = json.dumps(request, indent=4, default=str)
            with open(file_name, "a") as file:
                file.write(request_json + "\n")
            mturk_client.accept_qualification_request(QualificationRequestId=request_id)
            print(f"Approved and logged request: {request_id}")
    except Exception as e:
        print(f"An error occurred: {e}")


def serialize_datetime(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    raise TypeError("Type %s not serializable" % type(obj))


def preprocess_hit(hit):
    for key, value in hit.items():
        if isinstance(value, datetime.datetime):
            hit[key] = value.isoformat()
    return hit


def fetch_all_hits(mturk_client, cutoff_date, fetched_hits_file):
    print("Fetching all HITs from MTurk...")
    all_hits = []
    next_token = None
    while True:
        response = (
            mturk_client.list_hits(NextToken=next_token)
            if next_token
            else mturk_client.list_hits()
        )
        processed_hits = [
            preprocess_hit(hit)
            for hit in response["HITs"]
            if hit["CreationTime"].replace(tzinfo=timezone.utc) > cutoff_date
        ]
        all_hits.extend(processed_hits)
        next_token = response.get("NextToken")
        if not next_token:
            break
    with open(fetched_hits_file, "w") as file:
        json.dump(all_hits, file, default=serialize_datetime, indent=4)
    print("All HITs fetched and saved.")


def save_json(data, file_path):
    with open(file_path, "w") as file:
        json.dump(data, file, default=serialize_datetime, indent=4)


def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def load_cache(full_cache_path):
    return load_json(full_cache_path)


def save_cache(cache, full_cache_path):
    save_json(cache, full_cache_path)


def convert_to_utc(dt_input):
    if isinstance(dt_input, str):
        dt = datetime.datetime.fromisoformat(dt_input)
    elif isinstance(dt_input, datetime.datetime):
        dt = dt_input
    else:
        raise TypeError(
            f"Expected string or datetime for conversion, got {type(dt_input)}"
        )
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    else:
        return dt.replace(tzinfo=timezone.utc)


def check_hit_and_fetch_assignments(mturk_client, hit, cache, current_time):
    hit_id = hit["HITId"]
    expiration = convert_to_utc(hit["Expiration"])
    current_time = current_time.astimezone(timezone.utc)
    cache_hit = cache.get(hit_id)
    if cache_hit:
        cache_expiration = convert_to_utc(cache_hit["Expiration"])
        if cache_expiration < current_time or (
            cache_hit["NumberOfAssignmentsAvailable"] == 0
            and cache_hit["NumberOfAssignmentsPending"] == 0
        ):
            return {"hit_id": hit_id, "data": cache_hit["Data"]}
    assignments = mturk_client.list_assignments_for_hit(HITId=hit_id)["Assignments"]
    assignment_data = [
        {
            "HITId": hit_id,
            "AssignmentId": assn["AssignmentId"],
            "AssignmentStatus": assn["AssignmentStatus"],
            "AcceptTime": convert_to_utc(assn["AcceptTime"]).isoformat(),
            "SubmitTime": convert_to_utc(assn["SubmitTime"]).isoformat(),
            "Duration": convert_to_utc(assn["SubmitTime"])
            - convert_to_utc(assn["AcceptTime"]),
            "WorkerId": assn["WorkerId"],
            "Answer": assn["Answer"],
            "Question": mturk_client.get_hit(HITId=hit_id)["HIT"]["Question"],
        }
        for assn in assignments
    ]
    cache[hit_id] = {
        "Expiration": expiration.isoformat(),
        "NumberOfAssignmentsAvailable": hit["NumberOfAssignmentsAvailable"],
        "NumberOfAssignmentsPending": hit["NumberOfAssignmentsPending"],
        "Data": assignment_data,
    }
    return {"hit_id": hit_id, "data": assignment_data}


def count_non_expired_assignments_in_cache(full_cache_path):
    cache = load_cache(full_cache_path)
    current_time = datetime.datetime.now(timezone.utc)
    total_available = 0
    total_pending = 0
    for hit_id, hit_data in cache.items():
        expiration_time = datetime.datetime.fromisoformat(
            hit_data["Expiration"].replace("Z", "+00:00")
        )
        if expiration_time > current_time:
            total_available += hit_data.get("NumberOfAssignmentsAvailable", 0)
            total_pending += hit_data.get("NumberOfAssignmentsPending", 0)
    return total_available, total_pending


def get_hit_results(mturk_client, fetched_hits_file, full_cache_path):
    cache = load_cache(full_cache_path)
    hits = load_json(fetched_hits_file)
    current_time = datetime.datetime.now(timezone.utc)
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_hit = {
            executor.submit(
                check_hit_and_fetch_assignments, mturk_client, hit, cache, current_time
            ): hit
            for hit in hits
        }
        for future in concurrent.futures.as_completed(future_to_hit):
            result = future.result()
            if result:
                all_results.extend(result["data"])
    save_cache(cache, full_cache_path)
    return pd.DataFrame(all_results)


def extract_questions_from_xml(xml_file):
    with open(xml_file, "r") as file:
        question_xml = file.read()
    return extract_texts_from_xml(question_xml)


def extract_texts_from_xml(xml_q):
    parsed_question = parse_question_xml(xml_q)
    questions_123 = [
        question["Text"] for question in parsed_question if "Tekst" in question["Title"]
    ]
    return questions_123


def expire_all_active_hits(mturk_client):
    utc_now = datetime.datetime.now(pytz.UTC)
    utc_yesterday = utc_now - timedelta(days=1)
    next_token = None
    while True:
        response = (
            mturk_client.list_hits(NextToken=next_token)
            if next_token
            else mturk_client.list_hits()
        )
        for hit in response["HITs"]:
            mturk_client.update_expiration_for_hit(
                HITId=hit["HITId"], ExpireAt=utc_yesterday
            )
        next_token = response.get("NextToken")
        if not next_token:
            break


def reject_hit(mturk_client, assignment_id, hit_organizer):
    try:
        mturk_client.reject_assignment(
            AssignmentId=assignment_id,
            RequesterFeedback="Your work did not meet the required standards, as you had too few correct multiple choice answers or wrong sourcing. We encourage you to try again!",
        )
        hit_organizer.organize_file(assignment_id, approve=False)
        print(f"Rejected HIT: {assignment_id}")
    except mturk_client.exceptions.RequestError as e:
        print(f"Error: {e}")


def approve_hit(mturk_client, assignment_id, hit_organizer):
    try:
        mturk_client.approve_assignment(
            AssignmentId=assignment_id,
            RequesterFeedback="Good work, thank you!",
            OverrideRejection=False,
        )
        hit_organizer.organize_file(assignment_id, approve=True)
        print(f"Approved HIT: {assignment_id}")
    except mturk_client.exceptions.RequestError as e:
        print(f"Error: {e}")


def ban_worker(mturk_client, worker_id):
    try:
        mturk_client.create_worker_block(
            WorkerId=worker_id,
            Reason="Repeatedly submitting low-quality work",
        )
        print(f"Blocked Worker: {worker_id}")
    except mturk_client.exceptions.RequestError as e:
        print(f"Error: {e}")


def retrieve_and_count_questions(mturk_client, rejected_assignment_ids):
    questions_data = {}
    next_token = None
    while True:
        response = (
            mturk_client.list_hits(NextToken=next_token)
            if next_token
            else mturk_client.list_hits()
        )
        for hit in response["HITs"]:
            hit_id = hit["HITId"]
            question = hit["Question"]
            is_expired = hit["Expiration"] < datetime.datetime.now(timezone.utc)
            parsed_question = tuple(extract_texts_from_xml(question))
            if parsed_question not in questions_data:
                questions_data[parsed_question] = {
                    "total_count": 0,
                    "hit_ids": set(),
                    "question_xml": hit["Question"],
                }
            assignments_response = mturk_client.list_assignments_for_hit(HITId=hit_id)
            for assignment in assignments_response["Assignments"]:
                if (
                    assignment["AssignmentStatus"]
                    in ["Submitted", "Approved", "Pending"]
                    and assignment["AssignmentId"] not in rejected_assignment_ids
                ):
                    questions_data[parsed_question]["total_count"] += 1
            questions_data[parsed_question]["total_count"] += hit[
                "NumberOfAssignmentsPending"
            ]
            if not is_expired:
                questions_data[parsed_question]["total_count"] += hit[
                    "NumberOfAssignmentsAvailable"
                ]
            questions_data[parsed_question]["hit_ids"].add(hit_id)
        next_token = response.get("NextToken")
        if not next_token:
            break
    return questions_data


def retrieve_and_count_questions_from_cache(
    mturk_client, rejected_assignment_ids, fetched_hits_file
):
    questions_data = {}
    all_hits = load_json(fetched_hits_file)
    lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(
                process_hit_and_count_questions,
                hit,
                mturk_client,
                questions_data,
                lock,
                rejected_assignment_ids,
            )
            for hit in all_hits
        ]
        concurrent.futures.wait(futures)
    return questions_data


def process_hit_and_count_questions(
    hit, mturk_client, questions_data, lock, rejected_assignment_ids
):
    hit_id = hit["HITId"]
    question = hit["Question"]
    expiration = datetime.datetime.fromisoformat(hit["Expiration"]).replace(
        tzinfo=timezone.utc
    )
    is_expired = expiration < datetime.datetime.now(timezone.utc)
    parsed_question = tuple(extract_texts_from_xml(question))
    assignments_response = mturk_client.list_assignments_for_hit(HITId=hit_id)
    count = 0
    for assignment in assignments_response["Assignments"]:
        if (
            assignment["AssignmentStatus"] in ["Submitted", "Approved"]
            and assignment["AssignmentId"] not in rejected_assignment_ids
        ):
            count += 1
    with lock:
        if parsed_question not in questions_data:
            questions_data[parsed_question] = {
                "total_count": 0,
                "hit_ids": set(),
                "question_xml": question,
            }
        questions_data[parsed_question]["total_count"] += (
            count + hit["NumberOfAssignmentsPending"]
        )
        if not is_expired:
            questions_data[parsed_question]["total_count"] += hit[
                "NumberOfAssignmentsAvailable"
            ]
        questions_data[parsed_question]["hit_ids"].add(hit_id)


def create_consolidated_additional_hits(
    mturk_client, questions_data, qualification_type_id
):
    counter = 0
    ass_counter = 0
    for question, data in questions_data.items():
        try:
            with open(data["xml_file"], "r") as file:
                question_xml = file.read()
        except FileNotFoundError:
            print("File not found.")
            continue
        if data["total_count"] < 2:
            additional_assignments = 2 - data["total_count"]
            counter += 1
            ass_counter += additional_assignments
            new_hit_id = mturk_client.create_hit(
                Title="NorwAI Norwegian/Norsk Annotation",
                Description="Les en nyhetsartikkel og gi et sammendrag og svar på spørsmål.",
                Keywords="nyheter, annotering, sammendrag, lesing",
                Reward="6.00",
                MaxAssignments=additional_assignments,
                LifetimeInSeconds=1920000,
                AssignmentDurationInSeconds=1800,
                Question=question_xml,
                QualificationRequirements=[
                    {
                        "QualificationTypeId": qualification_type_id,
                        "Comparator": "Exists",
                        "ActionsGuarded": "Accept",
                    },
                    {
                        "QualificationTypeId": "000000000000000000L0",
                        "Comparator": "GreaterThan",
                        "IntegerValues": [60],
                        "ActionsGuarded": "Accept",
                    },
                ],
            )["HIT"]["HITId"]
            print(
                f"Created new HIT with ID: {new_hit_id} for question '{data['xml_file']}' with {additional_assignments} additional assignments."
            )
    return counter, ass_counter
