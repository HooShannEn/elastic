from handoff import detect_crisis, generate_referral_summary, escalate_to_worker

test_msg = 'I have no food at home tonight and my children are hungry'
if detect_crisis(test_msg):
    summary = generate_referral_summary(test_msg, {'age_range': '36-50', 'household_size': '3'})
    result = escalate_to_worker(summary, case_code='DEMO01')
    print(result['summary'])
    print(result['message'])
