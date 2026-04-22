import requests
from Config import ReadConfigFile
from Config import configfile

REPORT_DRIVE_URL = ReadConfigFile.ReadConfig.get_web_hook_details("REPORT_URL")
WEB_HOOK_URL = ReadConfigFile.ReadConfig.get_web_hook_details("WEB_HOOK_URL")
MENTION_TAG = f"<users/{ReadConfigFile.ReadConfig.get_web_hook_details("MANAGER_USER_ID")}>"


def send_google_chat_report(env, sprint, suite_name, total_suites, expected_suites, passed_suite, total_tcs, passed_testcases, expected_tcs=configfile.TARGET_EXECUTION_GOAL, commit_id="Unknown"):

    f_suite = total_suites - passed_suite
    failed_testcases = total_tcs - passed_testcases
    
    pass_rate = round((passed_testcases / total_tcs * 100), 1) if total_tcs > 0 else 0
    rate_color = "#008000" if pass_rate >= 95 else ("#F59E0B" if pass_rate >= 80 else "#FF0000")

    integrity_text = ""
    if total_suites == expected_suites:
        integrity_text = f" | <b><font color=#059669>Goal Target: {expected_tcs} Cases</font></b>"
    elif total_suites < expected_suites:
        integrity_text = f" | <b><font color=#EA580C>Data Integrity: {expected_suites - total_suites} Reports Missing</font></b>"
    else:
        integrity_text = f" | <b><font color=#4F46E5>Data Integrity: New Reports Added ({total_suites}/{expected_suites})</font></b>"

    # Determine status details based on failures
    if f_suite > 0:
        status = "FAILED"
        icon_url = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/cancel/default/48px.svg"
        result_color = "#FF0000" 
        summary_text = f"<b><font color=#DE5840>{f_suite} test suite(s) failed out of {total_suites}.</font></b>{integrity_text}"
    else:
        status = "PASSED"
        icon_url = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/check_circle/default/48px.svg"
        result_color = "#008000"
        summary_text = f"<b><font color=#42C255>All {total_suites} test suites passed successfully.</font></b>{integrity_text}"

    payload = {
        "text": f"{MENTION_TAG}: The test reports have been sent to your email. ✅",
        "cardsV2": [{
            "cardId": "testReport",
            "card": {
                "header": {
                    "title": f"Hirepro: {suite_name}",
                    "subtitle": f"Sprint: {sprint} | Environment: {env}",
                    "imageUrl": icon_url
                },
                "sections": [{
                    "widgets": [
                        {
                            "decoratedText": {
                                "startIcon": { "knownIcon": "STAR" },
                                "topLabel": "Audit Status",
                                "text": f"<b><font color=\"{result_color}\">{status}</font></b>",
                                "bottomLabel": summary_text
                            }
                        },
                        {
                            "columns": {
                                "columnItems": [
                                    {"widgets": [{"textParagraph": {"text": f"<b>Passed TCs: <font color=#008000>{passed_testcases}</font></b>"}}]},
                                    {"widgets": [{"textParagraph": {"text": f"<b>Failed TCs: <font color=#FF0000>{failed_testcases}</font></b>"}}]},
                                    {"widgets": [{"textParagraph": {"text": f"<b>Pass Rate: <font color={rate_color}>{pass_rate}%</font></b>"}}]}
                                ]
                            }
                        },
                        { "divider": {} },
                        {
                            "buttonList": {
                                "buttons": [{
                                    "text": "View Full Report",
                                    "type": "FILLED",
                                    "color": {
                                        "red": 0.56,
                                        "green": 0.93,
                                        "blue": 0.56,
                                        "alpha": 1.0

                                    },
                                    "onClick": { "openLink": { "url": REPORT_DRIVE_URL } }
                                }]
                            }
                        },
                        {
                            "textParagraph": {
                                "text": f"<font color=#64748b><i>Build ID: {commit_id}</i></font>"
                            }
                        }
                    ]
                }]
            }
        }]
    }

    response = requests.post(WEB_HOOK_URL, json=payload)
    return response.status_code

# Example Usage:
# send_google_chat_report(env="QA",
#                         sprint=217,
#                         suite_name="ALL Reports",
#                         total_suites=49,
#                         passed_suite=49,
#                         total_tcs=49,
#                         passed_testcases=226)