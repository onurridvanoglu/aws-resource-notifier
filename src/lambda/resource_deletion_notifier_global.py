#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS Resource Deletion Notifier Global (us-east-1) Lambda Function

This Lambda function processes CloudTrail events for AWS resource deletion
and sends notifications to a Microsoft Teams channel.
"""

import json
import os
import urllib.request
import urllib.parse
import urllib.error
import boto3
from datetime import datetime
import logging
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')


def svg_to_data_url(svg_content):
    """Convert SVG content to a data URL format."""
    svg_bytes = svg_content.encode('utf-8')
    base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{base64_svg}"


def get_webhook_url():
    """Retrieve the Microsoft Teams webhook URL from Secrets Manager."""
    secret_name = os.environ['TEAMS_WEBHOOK_SECRET_NAME']
    
    try:
        response = secretsmanager.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(response['SecretString'])
        return secret['webhookUrl']
    except Exception as e:
        logger.error(f"Error retrieving webhook URL: {str(e)}")
        raise


def get_service_icon(resource_type):
    """Get the appropriate AWS service icon URL based on resource type."""
    # Map resource types to official AWS Architecture Icons (as SVG URLs)
    icon_mapping = {
        'IAM User': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_AWS-Single-Sign-On_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#BD0816" offset="0%"></stop>
            <stop stop-color="#FF5252" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_AWS-Single-Sign-On_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Security-Identity-Compliance" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M67.438,62.3245478 L52.56,47.4465478 C52.251,47.1385478 52.178,46.6655478 52.379,46.2795478 C54.457,42.2765478 53.659,37.2315478 50.439,34.0115478 C48.143,31.7155478 44.972,30.6245478 41.748,31.0125478 C38.518,31.4035478 35.67,33.2675478 33.936,36.1285478 C31.898,39.4875478 31.989,43.7965478 34.166,47.1075478 C37.187,51.7025478 43.076,53.2915478 47.864,50.8085478 C48.251,50.6085478 48.722,50.6805478 49.032,50.9895478 L51.5,53.4575478 C51.687,53.6445478 51.792,53.8995478 51.792,54.1645478 L51.792,57.4075478 L55.035,57.4075478 C55.299,57.4075478 55.554,57.5125478 55.742,57.6995478 L57.157,59.1135478 C57.344,59.3015478 57.45,59.5555478 57.45,59.8215478 L57.45,63.0635478 L60.692,63.0635478 C60.958,63.0635478 61.211,63.1695478 61.399,63.3565478 L63.254,65.2125478 L67.196,65.4755478 L67.438,62.3245478 Z M69.467,62.0195478 L69.114,66.6155478 C69.074,67.1395478 68.636,67.5385478 68.118,67.5385478 C68.095,67.5385478 68.073,67.5385478 68.05,67.5365478 L62.747,67.1825478 C62.504,67.1665478 62.277,67.0635478 62.106,66.8925478 L60.278,65.0635478 L56.45,65.0635478 C55.897,65.0635478 55.45,64.6165478 55.45,64.0635478 L55.45,60.2355478 L54.621,59.4075478 L50.792,59.4075478 C50.24,59.4075478 49.792,58.9595478 49.792,58.4075478 L49.792,54.5785478 L48.12,52.9055478 C42.546,55.3915478 35.941,53.4495478 32.494,48.2065478 C29.896,44.2545478 29.791,39.1065478 32.225,35.0915478 C34.281,31.7015478 37.665,29.4915478 41.507,29.0275478 C45.349,28.5655478 49.12,29.8645478 51.853,32.5975478 C55.506,36.2505478 56.536,41.8835478 54.475,46.5335478 L69.177,61.2355478 C69.383,61.4425478 69.49,61.7285478 69.467,62.0195478 L69.467,62.0195478 Z M45.423,41.3455478 C45.423,40.6775478 45.163,40.0495478 44.69,39.5775478 C44.217,39.1045478 43.589,38.8445478 42.922,38.8445478 C42.255,38.8445478 41.627,39.1045478 41.155,39.5765478 C40.18,40.5515478 40.18,42.1375478 41.155,43.1125478 C42.129,44.0875478 43.715,44.0875478 44.69,43.1125478 L44.69,43.1125478 C45.163,42.6395478 45.423,42.0125478 45.423,41.3455478 L45.423,41.3455478 Z M46.104,38.1625478 C46.955,39.0125478 47.423,40.1425478 47.423,41.3455478 C47.423,42.5465478 46.955,43.6765478 46.104,44.5265478 L46.104,44.5275478 C45.227,45.4045478 44.075,45.8425478 42.922,45.8425478 C41.77,45.8425478 40.618,45.4045478 39.741,44.5265478 C37.987,42.7715478 37.987,39.9165478 39.741,38.1625478 C40.59,37.3125478 41.72,36.8445478 42.922,36.8445478 C44.125,36.8445478 45.254,37.3125478 46.104,38.1625478 L46.104,38.1625478 Z M22.001,44.9215478 L28,44.9215478 L28,46.9215478 L22,46.9215478 C16.146,46.9085478 11.326,42.7565478 11.024,37.4675478 C11.011,37.2175478 11,36.9865478 11,36.7545478 C11,30.2305478 15.627,27.8055478 18.351,26.9445478 C18.333,26.6565478 18.324,26.3655478 18.324,26.0695478 C18.324,20.7195478 22.081,15.1815478 27.063,13.1885478 C32.87,10.8445478 39.028,12.0105478 43.526,16.3065478 C44.713,17.4265478 46.231,19.1005478 47.295,21.1415478 C48.431,20.1435478 49.714,19.6545478 51.183,19.6545478 C54.086,19.6545478 57.34,21.9905478 57.931,27.0965478 C63.95,28.4715478 67,31.7745478 67,36.9215478 C67,42.3485478 63.778,45.9895478 58.161,46.9085478 L57.838,44.9345478 C61.105,44.4005478 65,42.5755478 65,36.9215478 C65,32.5405478 62.397,29.9925478 56.808,28.9035478 C56.361,28.8155478 56.029,28.4365478 56.001,27.9815478 C55.777,24.2565478 53.795,21.6545478 51.183,21.6545478 C49.848,21.6545478 48.801,22.2345478 47.789,23.5355478 C47.566,23.8215478 47.209,23.9635478 46.848,23.9105478 C46.491,23.8555478 46.19,23.6115478 46.063,23.2725478 C45.191,20.9425478 43.454,18.9875478 42.15,17.7575478 C38.231,14.0155478 32.872,13.0035478 27.808,15.0445478 C23.61,16.7235478 20.324,21.5665478 20.324,26.0695478 C20.324,26.5745478 20.354,27.0605478 20.417,27.5545478 C20.421,27.5915478 20.423,27.6295478 20.424,27.6675478 L20.424,27.6695478 L20.424,27.6715478 L20.424,27.6735478 L20.424,27.6755478 L20.424,27.6755478 L20.424,27.6775478 L20.424,27.6775478 L20.424,27.6785478 L20.424,27.6795478 L20.424,27.6815478 C20.424,28.1865478 20.05,28.6085478 19.564,28.6775478 C17.065,29.3115478 13,31.1975478 13,36.7545478 C13,36.9515478 13.01,37.1485478 13.02,37.3375478 C13.262,41.5865478 17.208,44.9115478 22.001,44.9215478 L22.001,44.9215478 Z" id="AWS-Single-Sign-On_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'Route53 DNS Record': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_Amazon-Route-53_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#4D27A8" offset="0%"></stop>
            <stop stop-color="#A166FF" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Amazon-Route-53_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Networking-Content-Delivery" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M48.692,40.6795109 C49.431,41.3627732 49.801,42.2781246 49.801,43.4275659 C49.801,44.678046 49.351,45.6764293 48.452,46.4227159 C47.552,47.1700028 46.343,47.543146 44.826,47.543146 C43.627,47.543146 42.44,47.2870477 41.266,46.7768518 L41.266,45.2452638 C42.657,45.7054405 43.843,45.9345284 44.826,45.9345284 C45.796,45.9345284 46.542,45.7174451 47.065,45.2842788 C47.588,44.8501121 47.849,44.2308744 47.849,43.4275659 C47.849,41.8829729 46.874,41.1106764 44.921,41.1106764 C44.309,41.1106764 43.703,41.1426887 43.103,41.2057129 L43.103,39.9432282 L47.123,35.5585448 L41.458,35.5585448 L41.458,33.9889422 L49.247,33.9889422 L49.247,35.5015229 L45.304,39.6751253 C45.369,39.6621203 45.431,39.656118 45.496,39.656118 L45.687,39.656118 C46.951,39.656118 47.952,39.9972489 48.692,40.6795109 M37.574,40.3453826 C38.351,41.0726618 38.74,42.0740463 38.74,43.349536 C38.74,44.6010165 38.288,45.6124048 37.381,46.3847013 C36.475,47.1569978 35.283,47.543146 33.803,47.543146 C32.503,47.543146 31.284,47.2870477 30.148,46.7768518 L30.148,45.2452638 C31.564,45.7054405 32.776,45.9345284 33.784,45.9345284 C34.754,45.9345284 35.497,45.7154443 36.013,45.2742749 C36.53,44.834106 36.789,44.1998624 36.789,43.3695437 C36.789,42.4631957 36.546,41.8059434 36.061,41.3977867 C35.576,40.9896299 34.785,40.7845512 33.688,40.7845512 C32.897,40.7845512 31.909,40.8495762 30.722,40.976625 L30.722,39.7131399 L31.086,33.9889422 L38.071,33.9889422 L38.071,35.5585448 L32.693,35.5585448 L32.444,39.4450369 C33.146,39.3179882 33.777,39.2539636 34.338,39.2539636 C35.716,39.2539636 36.795,39.617103 37.574,40.3453826 M51.957,54.37777 C47.103,55.250105 42.852,57.2268639 40,58.8374822 C37.147,57.2268639 32.896,55.250105 28.043,54.37777 C26.677,54.1326759 19.869,52.7111302 19.869,48.7756192 C19.869,46.951919 20.522,45.7424547 21.776,43.5826255 C23.274,40.9996338 25.138,37.7843994 25.138,33.1556222 C25.138,29.8473521 24.271,26.6751342 22.559,23.7149977 C22.76,23.4669025 22.965,23.2158061 23.171,22.9627089 C25.707,24.2301955 28.347,24.8724421 31.031,24.8724421 C34.311,24.8724421 37.325,24.0111114 40,22.3114589 C42.674,24.0111114 45.688,24.8724421 48.968,24.8724421 C51.652,24.8724421 54.293,24.2301955 56.829,22.9627089 C57.034,23.2158061 57.239,23.4669025 57.44,23.7149977 C55.728,26.6751342 54.861,29.8473521 54.861,33.1556222 C54.861,37.7843994 56.725,40.9996338 58.226,43.586627 C59.477,45.7424547 60.13,46.951919 60.13,48.7756192 C60.13,52.7111302 53.322,54.1326759 51.957,54.37777 M56.861,33.1556222 C56.861,29.9974097 57.752,26.9702475 59.507,24.1581679 C59.735,23.7950284 59.706,23.3278491 59.434,22.9957216 C58.926,22.3734827 58.393,21.7182311 57.867,21.0669811 C57.562,20.6898363 57.032,20.5857963 56.606,20.8198862 C54.143,22.1814089 51.574,22.8716739 48.968,22.8716739 C45.824,22.8716739 43.077,22.0263494 40.569,20.2886823 C40.227,20.0515912 39.772,20.0515912 39.43,20.2886823 C36.922,22.0263494 34.175,22.8716739 31.031,22.8716739 C28.425,22.8716739 25.856,22.1814089 23.393,20.8198862 C22.968,20.5857963 22.437,20.6898363 22.132,21.0669811 C21.606,21.7182311 21.073,22.3734827 20.565,22.9957216 C20.294,23.3278491 20.264,23.7950284 20.492,24.1581679 C22.248,26.9702475 23.138,29.9974097 23.138,33.1556222 C23.138,37.2461927 21.423,40.2023277 20.045,42.581241 C18.695,44.9041328 17.869,46.4467251 17.869,48.7756192 C17.869,54.1646882 25.385,55.9343677 27.689,56.3475263 C32.549,57.2208616 36.793,59.2806524 39.497,60.8542565 C39.652,60.9452915 39.826,60.9903088 40,60.9903088 C40.173,60.9903088 40.347,60.9452915 40.503,60.8542565 C43.207,59.2806524 47.45,57.2208616 52.31,56.3475263 C54.614,55.9343677 62.13,54.1646882 62.13,48.7756192 C62.13,46.4467251 61.304,44.9041328 59.954,42.5782399 C58.576,40.2023277 56.861,37.2461927 56.861,33.1556222 M52.994,60.1569888 C46.863,61.2594121 41.723,64.556678 40,65.7641416 C38.276,64.556678 33.136,61.2594121 27.005,60.1569888 C14.937,57.9891566 14,50.8974338 14,48.7756192 C14,45.2852792 15.371,42.9233724 16.697,40.6374948 C17.961,38.4596586 19.268,36.2067937 19.268,33.1556222 C19.268,28.3357718 16.485,24.9314648 15.112,23.5459328 C16.556,21.7892584 20.204,17.3415508 22.003,15.0236609 C24.729,17.5966487 27.898,19.0001876 31.031,19.0001876 C34.509,19.0001876 37.385,17.5846441 40,14.5644846 C42.614,17.5846441 45.49,19.0001876 48.968,19.0001876 C52.101,19.0001876 55.27,17.5966487 57.997,15.0236609 C59.796,17.3415508 63.443,21.7892584 64.887,23.5459328 C63.514,24.9314648 60.731,28.3357718 60.731,33.1556222 C60.731,36.2067937 62.039,38.4596586 63.302,40.6374948 C64.629,42.9233724 66,45.2852792 66,48.7756192 C66,50.8974338 65.062,57.9891566 52.994,60.1569888 M65.032,39.6341095 C63.797,37.5052922 62.731,35.6675867 62.731,33.1556222 C62.731,27.867592 66.847,24.4472789 66.887,24.4152666 C67.094,24.2472021 67.226,24.0031083 67.254,23.7370062 C67.28,23.470904 67.2,23.2058022 67.03,22.9997231 C66.963,22.9196924 60.408,14.9726413 58.906,12.9138509 C58.73,12.6727583 58.457,12.5227007 58.159,12.5046938 C57.86,12.4826853 57.572,12.601731 57.368,12.8198148 C54.848,15.5148495 51.866,16.9994194 48.968,16.9994194 C45.764,16.9994194 43.244,15.5718713 40.794,12.3706423 C40.415,11.8764526 39.585,11.8764526 39.206,12.3706423 C36.755,15.5718713 34.235,16.9994194 31.031,16.9994194 C28.133,16.9994194 25.151,15.5148495 22.631,12.8198148 C22.427,12.601731 22.137,12.4776834 21.84,12.5046938 C21.543,12.5227007 21.269,12.6727583 21.093,12.9138509 C19.591,14.9726413 13.036,22.9196924 12.969,22.9997231 C12.8,23.2058022 12.72,23.470904 12.747,23.7360058 C12.773,24.0011076 12.904,24.2452013 13.11,24.4132658 C13.152,24.4472789 17.268,27.867592 17.268,33.1556222 C17.268,35.6675867 16.202,37.5052922 14.967,39.6341095 C13.576,42.0310298 12,44.7470725 12,48.7756192 C12,55.487196 17.477,60.4781121 26.652,62.1267451 C33.559,63.3682217 39.334,67.7489036 39.391,67.7939209 C39.57,67.9309735 39.785,68 40,68 C40.214,68 40.429,67.9309735 40.609,67.7929205 C40.667,67.7489036 46.422,63.3712229 53.347,62.1267451 C62.522,60.4781121 68,55.487196 68,48.7756192 C68,44.7470725 66.423,42.0310298 65.032,39.6341095" id="Amazon-Route-53-Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>''')
    }
    
    # Return the appropriate icon URL or a default AWS icon
    return icon_mapping.get(resource_type, "https://d1.awsstatic.com/webteam/architecture-icons/q42023/Res_AWS-Logo_48.svg")


def get_resource_info(event_detail):
    """Extract resource information based on the event type."""
    
    event_source = event_detail.get('eventSource', '')
    event_name = event_detail.get('eventName', '')
    
    # Default resource info structure
    resource_info = {
        'resourceType': 'Unknown',
        'resourceName': 'Unknown',
        'resourceId': 'Unknown',
        'additionalInfo': {}
    }
    
    # IAM User Deletion
    if event_source == 'iam.amazonaws.com' and event_name == 'DeleteUser':
        request_params = event_detail.get('requestParameters', {})
        user_name = request_params.get('userName')
        resource_info = {
            'resourceType': 'IAM User',
            'resourceName': user_name,
            'resourceId': user_name,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown')
            }
        }
    
    # Route53 DNS Record Deletion
    elif event_source == 'route53.amazonaws.com' and event_name == 'ChangeResourceRecordSets':
        request_params = event_detail.get('requestParameters', {})
        changes = request_params.get('changeBatch', {}).get('changes', [])
        
        if changes:
            change = changes[0]
            if change.get('action') == 'DELETE':
                record_set = change.get('resourceRecordSet', {})
                hosted_zone_id = request_params.get('hostedZoneId', 'Unknown')
                if hosted_zone_id and hosted_zone_id.startswith('/hostedzone/'):
                    hosted_zone_id = hosted_zone_id.split('/hostedzone/')[-1]
                
                resource_info = {
                    'resourceType': 'Route53 DNS Record',
                    'resourceName': record_set.get('name', 'Unknown'),
                    'resourceId': f"{hosted_zone_id}/{record_set.get('name', 'Unknown')}/{record_set.get('type', 'Unknown')}",
                    'additionalInfo': {
                        'hostedZoneId': hosted_zone_id,
                        'recordType': record_set.get('type', 'Unknown'),
                        'region': event_detail.get('awsRegion', 'Unknown')
                    }
                }
    
    return resource_info


def create_teams_message(event, resource_info):
    """Create a formatted Microsoft Teams card message with a modern credit card design."""
    
    # Get event details
    event_time = event.get('detail', {}).get('eventTime', 'Unknown')
    aws_region = event.get('detail', {}).get('awsRegion', 'Unknown')
    event_source = event.get('detail', {}).get('eventSource', 'Unknown').split('.')[0]
    user_identity = event.get('detail', {}).get('userIdentity', {})
    
    # Format the user information
    user_type = user_identity.get('type', 'Unknown')
    user_name = 'Unknown'
    
    if user_type == 'IAMUser':
        user_name = user_identity.get('userName', 'Unknown')
    elif user_type == 'AssumedRole':
        session_context = user_identity.get('sessionContext', {})
        user_name = session_context.get('sessionIssuer', {}).get('userName', 'Unknown')
    elif user_type == 'Root':
        user_name = 'Root User'
    
    # Format the event time
    try:
        event_datetime = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%SZ')
        formatted_time = event_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = event_time
    
    # Get service icon
    service_icon = get_service_icon(resource_info['resourceType'])
    
    # Create the Teams message card with modern credit card style design
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "C43532", 
        "summary": f"{resource_info['resourceType']} Deleted",
        "sections": [
            {
                "activityTitle": "",
                "activitySubtitle": "",
                "text": f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px;">
    <div style="background: linear-gradient(135deg, #C43532 0%, #FF6666 100%); border-radius: 12px; padding: 20px; color: white; margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h2 style="margin: 0; font-size: 22px; font-weight: 600;">⚠️ RESOURCE DELETED</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px; opacity: 0.9;">{resource_info['resourceType']}</p>
            </div>
            <img src="{service_icon}" width="48" height="48" style="filter: brightness(0) invert(1); margin-left: 15px;" />
        </div>
        <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <p style="margin: 0; font-size: 14px; opacity: 0.9; font-weight: 500;">RESOURCE ID</p>
                <p style="margin: 0; font-size: 16px; font-family: 'Courier New', monospace; letter-spacing: 1px;">{resource_info['resourceId'][:22]}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; font-size: 14px; opacity: 0.9; font-weight: 500;">DELETED BY</p>
                <p style="margin: 0; font-size: 16px;">{user_name}</p>
            </div>
        </div>
    </div>
    
    <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin: 0 0 15px 0; color: #C43532; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px;">📊 RESOURCE DETAILS</h3>
        <div style="display: flex; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; margin-bottom: 10px;">
                <p style="margin: 0; font-size: 12px; color: #444; font-weight: 600;">RESOURCE NAME</p>
                <p style="margin: 5px 0 0 0; font-size: 15px; font-weight: 500; color: #222;">{resource_info['resourceName']}</p>
            </div>
            <div style="flex: 1; min-width: 200px; margin-bottom: 10px;">
                <p style="margin: 0; font-size: 12px; color: #444; font-weight: 600;">REGION</p>
                <p style="margin: 5px 0 0 0; font-size: 15px; font-weight: 500; color: #222;">{aws_region}</p>
            </div>
            <div style="flex: 1; min-width: 200px; margin-bottom: 10px;">
                <p style="margin: 0; font-size: 12px; color: #444; font-weight: 600;">TIMESTAMP</p>
                <p style="margin: 5px 0 0 0; font-size: 15px; font-weight: 500; color: #222;">{formatted_time}</p>
            </div>
            <div style="flex: 1; min-width: 200px; margin-bottom: 10px;">
                <p style="margin: 0; font-size: 12px; color: #444; font-weight: 600;">USER TYPE</p>
                <p style="margin: 5px 0 0 0; font-size: 15px; font-weight: 500; color: #222;">{user_type}</p>
            </div>
        </div>""",
                "markdown": True
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "🔗 View in AWS Console",
                "targets": [
                    {
                        "os": "default",
                        "uri": f"https://{aws_region}.console.aws.amazon.com"
                    }
                ]
            },
            {
                "@type": "OpenUri",
                "name": "📚 View AWS Documentation",
                "targets": [
                    {
                        "os": "default",
                        "uri": "https://docs.aws.amazon.com"
                    }
                ]
            }
        ]
    }
    
    # Add additional info section only if there are additional facts
    if resource_info['additionalInfo']:
        additional_info_html = """
        <h3 style="margin: 15px 0 15px 0; color: #C43532; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px;">📙 ADDITIONAL INFORMATION</h3>
        <div style="display: flex; flex-wrap: wrap;">
        """
        
        for key, value in resource_info['additionalInfo'].items():
            additional_info_html += f"""
            <div style="flex: 1; min-width: 200px; margin-bottom: 10px;">
                <p style="margin: 0; font-size: 12px; color: #444; font-weight: 600;">{key.upper()}</p>
                <p style="margin: 5px 0 0 0; font-size: 15px; font-weight: 500; color: #222;">{value}</p>
            </div>"""
        
        additional_info_html += """
        </div>
    </div>
</div>"""
        
        message["sections"][0]["text"] += additional_info_html
    else:
        message["sections"][0]["text"] += """
        </div>
    </div>
</div>"""
    
    return message


def send_teams_notification(webhook_url, message):
    """Send a notification to Microsoft Teams."""
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(webhook_url, data, headers)
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            logger.info(f"Teams notification sent successfully. Response: {response_data}")
            
        return True
    except Exception as e:
        logger.error(f"Error sending Teams notification: {str(e)}")
        return False


def lambda_handler(event, context):
    """Lambda function handler."""
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if this is a CloudTrail event
        if 'detail' not in event or 'eventSource' not in event['detail']:
            logger.warning("Not a valid CloudTrail event.")
            return {
                'statusCode': 400,
                'body': 'Not a valid CloudTrail event'
            }
        
        # Extract resource information
        resource_info = get_resource_info(event['detail'])
        
        # Skip processing if resource_info is None
        if resource_info is None:
            logger.info("Skipping event processing as no resource information could be extracted")
            return {
                'statusCode': 200,
                'body': 'Event skipped - no resource information'
            }
        
        # Get the webhook URL
        webhook_url = get_webhook_url()
        
        # Create and send Teams message
        teams_message = create_teams_message(event, resource_info)
        send_successful = send_teams_notification(webhook_url, teams_message)
        
        if send_successful:
            return {
                'statusCode': 200,
                'body': f"Notification sent for {resource_info['resourceType']} deletion: {resource_info['resourceName']}"
            }
        else:
            return {
                'statusCode': 500,
                'body': 'Failed to send Teams notification'
            }
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        } 