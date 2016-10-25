import filecmp
import os
import pprint

from behave import when, then, given

MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = \
    'MediaConch implementation check result:'
MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX = \
    'MediaConch policy check result'
POLICIES_DIR = 'mediaconch-policies'


@when('the user waits for the "{microservice_name}" micro-service to complete'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_sel_cli.await_job_completion(
        microservice_name, uuid_val, unit_type=unit_type)


@when('the user waits for the "{microservice_name}" decision point to appear'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    job_uuid, job_output = context.am_sel_cli.await_decision_point(
        microservice_name, uuid_val, unit_type=unit_type)
    context.scenario.awaiting_job_uuid = job_uuid


@when('the user chooses "{choice}" at decision point "{decision_point}" during'
      ' {unit_type}')
def step_impl(context, choice, decision_point, unit_type):
    step = ('when the user waits for the "{}" decision point to appear during'
            ' {}'.format(decision_point, unit_type))
    context.execute_steps(step)
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_sel_cli.make_choice(
        choice, decision_point, uuid_val, unit_type=unit_type)


@when('the user downloads the AIP')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    transfer_name = context.scenario.transfer_name
    context.scenario.aip_path = context.am_sel_cli.download_aip(
        transfer_name, uuid_val)


@when('the user decompresses the AIP')
def step_impl(context):
    context.scenario.aip_path = context.am_sel_cli.decompress_aip(
        context.scenario.aip_path)


@then('the logs directory of the AIP contains a copy of the MediaConch policy'
      ' file {policy_file}')
def step_impl(context, policy_file):
    aip_path = context.scenario.aip_path
    original_policy_path = os.path.join(POLICIES_DIR, policy_file)
    aip_policy_path = os.path.join(aip_path, 'data', 'logs', policy_file)
    assert os.path.isfile(original_policy_path)
    assert os.path.isfile(aip_policy_path)
    assert filecmp.cmp(original_policy_path, aip_policy_path)


@then('the "{microservice_name}" micro-service output is'
      ' "{microservice_output}" during {unit_type}')
def step_impl(context, microservice_name, microservice_output, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.scenario.job = context.am_sel_cli.parse_job(
        microservice_name, uuid_val, unit_type=unit_type)
    assert context.scenario.job.get('job_output') == microservice_output


###############################################################################
# FEATURE: PRE-INGEST CONFORMANCE CHECK
###############################################################################


@given('directory {transfer_path} contains files that are all {file_validity}'
       ' .mkv')
def step_impl(context, transfer_path, file_validity):
    pass


@then('validation micro-service output is {microservice_output}')
def step_impl(context, microservice_output):
    context.scenario.job = context.am_sel_cli.parse_job(
        'Validate formats', context.scenario.transfer_uuid)
    assert context.scenario.job.get('job_output') == microservice_output


@then('Archivematica continues processing')
def step_impl(context):
    print('Archivematica continues processing')


###############################################################################
# FEATURE: POST-NORMALIZATION CONFORMANCE CHECK
###############################################################################

# TODO: How to implement the following givens? Using SS API? Necessary?


@given('directory {transfer_path} contains files that will all be normalized'
       ' to {file_validity} .mkv')
def step_impl(context, transfer_path, file_validity):
    pass


@given('directory {transfer_path} contains a processing config that does'
       ' normalization for preservation, etc.')
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for preservation, approves normalization, and creates an
    AIP without storing it
    """
    pass


@given('directory {transfer_path} contains a processing config that does'
       ' normalization for access, etc.')
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for access, approves normalization, and creates an
    AIP without storing it
    """
    pass


# MKV-to-MKV (!) just for testing policy checks on access derivatives.
@when('the user edits the FPR rule to transcode .mkv files to .mkv for access')
def step_impl(context):
    context.am_sel_cli.change_normalization_rule_command(
        'Access Generic MKV',
        'Transcoding to mkv with ffmpeg')


@when('the user edits the FPR rule to transcode .mov files to .mkv for access')
def step_impl(context):
    context.am_sel_cli.change_normalization_rule_command(
        'Access Generic MOV',
        'Transcoding to mkv with ffmpeg')


@when('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    context.scenario.transfer_path = os.path.join(
        context.TRANSFER_SOURCE_PATH, transfer_path)
    context.scenario.transfer_name = context.am_sel_cli.unique_name(
        transfer_path2name(transfer_path))
    context.scenario.transfer_uuid = context.am_sel_cli.start_transfer(
        context.scenario.transfer_path, context.scenario.transfer_name)


@then('validate preservation derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    ingest_ms_output_is('Validate preservation derivatives',
                        microservice_output, context)


@then('validate access derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    ingest_ms_output_is('Validate access derivatives', microservice_output,
                        context)


@then('all preservation conformance checks in the normalization report have'
      ' value {validation_result}')
def step_impl(context, validation_result):
    all_normalization_report_columns_are(
        'preservation_conformance_check', validation_result, context)


@then('all access conformance checks in the normalization report have value'
      ' {validation_result}')
def step_impl(context, validation_result):
    all_normalization_report_columns_are(
        'access_conformance_check', validation_result, context)


@then('all PREMIS implementation-check-type validation events have'
      ' eventOutcome = {event_outcome}')
def step_impl(context, event_outcome):
    events = []
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.scenario.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))):
        if (e['event_type'] == 'validation' and
            e['event_detail'].startswith(MC_EVENT_DETAIL_PREFIX) and
            e['event_outcome_detail_note'].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX)):
            events.append(e)
    assert len(events) > 0
    for e in events:
        assert e['event_outcome'] == event_outcome


###############################################################################
# INGEST POLICY CHECK
###############################################################################


@given('MediaConch policy file {policy_file} is present in the local'
       ' mediaconch-policies/ directory')
def step_impl(context, policy_file):
    assert policy_file in os.listdir(POLICIES_DIR)


@given('directory {transfer_path} contains files that, when normalized, will'
       ' all {do_files_conform} to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given('directory {transfer_path}/manualNormalization/preservation/ contains a'
       ' file manually normalized for preservation that will'
       '{do_files_conform} to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given('directory {transfer_path}/manualNormalization/access/ contains a'
       ' file manually normalized for access that will {do_files_conform}'
       ' to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@when('the user uploads the policy file {policy_file}')
def step_impl(context, policy_file):
    policy_path = get_policy_path(policy_file)
    context.am_sel_cli.upload_policy(policy_path)


@when('the user ensures there is an FPR command that uses policy file'
      ' {policy_file}')
def step_impl(context, policy_file):
    context.am_sel_cli.ensure_fpr_policy_check_command(policy_file)


# TODO: this step could be generalized to support any purpose/format/command
# triple.
@when('the user ensures there is an FPR rule with purpose {purpose} that'
      ' validates Generic MKV files against policy file {policy_file}')
def step_impl(context, purpose, policy_file):
    context.am_sel_cli.ensure_fpr_rule(
        purpose,
        'Video: Matroska: Generic MKV',
        context.am_sel_cli.get_policy_command_description(policy_file)
    )


@then('policy checks for preservation derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    name = 'Policy checks for preservation derivatives'
    ingest_ms_output_is(name, microservice_output, context)


@then('policy checks for access derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    name = 'Policy checks for access derivatives'
    ingest_ms_output_is(name, microservice_output, context)


@then('all policy check for access derivatives tasks indicate {event_outcome}')
def step_impl(context, event_outcome):
    policy_check_tasks = [t for t in context.scenario.job['tasks'].values() if
                          t['stdout'].startswith(
                              'Running Check against policy ')]
    assert len(policy_check_tasks) > 0
    if event_outcome == 'pass':
        for task in policy_check_tasks:
            assert 'All policy checks passed:' in task['stdout']
            assert task['exit_code'] == '0'
    else:
        for task in policy_check_tasks:
            assert '"eventOutcomeInformation": "fail"' in task['stdout']


@then('all PREMIS policy-check-type validation events have eventOutcome ='
      ' {event_outcome}')
def step_impl(context, event_outcome):
    events = []
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.scenario.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))):
        if (e['event_type'] == 'validation' and
            e['event_detail'].startswith(MC_EVENT_DETAIL_PREFIX) and
            e['event_outcome_detail_note'].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX)):
            events.append(e)
    assert len(events) > 0
    for e in events:
        assert e['event_outcome'] == event_outcome


###############################################################################
# HELPER FUNCS
###############################################################################


def ingest_ms_output_is(name, output, context):
    """Wait for the Ingest micro-service with name ``name`` to appear and
    assert that its output is ``output``.
    """
    context.scenario.sip_uuid = context.am_sel_cli.get_sip_uuid(
        context.scenario.transfer_name)
    context.scenario.job = context.am_sel_cli.parse_job(
        name, context.scenario.sip_uuid, 'sip')
    assert context.scenario.job.get('job_output') == output


def all_normalization_report_columns_are(column, expected_value, context):
    """Wait for the normalization report to be generated then assert that all
    values in ``column`` have value ``expected_value``.
    """
    normalization_report = context.am_sel_cli.parse_normalization_report(
        context.scenario.sip_uuid)
    for file_dict in normalization_report:
        if file_dict['file_format'] != 'None':
            assert file_dict[column] == expected_value


def transfer_path2name(transfer_path):
    """Return a transfer name, given a transfer path."""
    return os.path.split(transfer_path.replace('-', '_'))[1]


def get_policy_path(policy_file):
    return os.path.realpath(os.path.join(POLICIES_DIR, policy_file))


def get_normalized_unit_type(unit_type):
    return {'transfer': 'transfer'}.get(unit_type, 'sip')


def get_uuid_val(context, unit_type):
    """Return the UUID value corresponding to the ``unit_type`` ('transfer' or
    'sip') of the unit being tested in this scenario.
    """
    if unit_type == 'transfer':
        uuid_val = context.scenario.transfer_uuid
    else:
        uuid_val = getattr(context.scenario, 'sip_uuid', None)
        if not uuid_val:
            uuid_val = context.scenario.sip_uuid = \
                context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name)
    return uuid_val
