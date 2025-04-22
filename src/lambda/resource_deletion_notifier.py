#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS Resource Deletion Notifier Lambda Function

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
ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')
rds_client = boto3.client('rds')
lambda_client = boto3.client('lambda')
elb_client = boto3.client('elbv2')


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
        'EC2 Instance': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_Amazon-EC2_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#C8511B" offset="0%"></stop>
            <stop stop-color="#FF9900" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Amazon-EC2_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Compute" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M27,53 L52,53 L52,28 L27,28 L27,53 Z M54,28 L58,28 L58,30 L54,30 L54,34 L58,34 L58,36 L54,36 L54,39 L58,39 L58,41 L54,41 L54,45 L58,45 L58,47 L54,47 L54,51 L58,51 L58,53 L54,53 L54,53.136 C54,54.164 53.164,55 52.136,55 L52,55 L52,59 L50,59 L50,55 L46,55 L46,59 L44,59 L44,55 L41,55 L41,59 L39,59 L39,55 L35,55 L35,59 L33,59 L33,55 L29,55 L29,59 L27,59 L27,55 L26.864,55 C25.836,55 25,54.164 25,53.136 L25,53 L22,53 L22,51 L25,51 L25,47 L22,47 L22,45 L25,45 L25,41 L22,41 L22,39 L25,39 L25,36 L22,36 L22,34 L25,34 L25,30 L22,30 L22,28 L25,28 L25,27.864 C25,26.836 25.836,26 26.864,26 L27,26 L27,22 L29,22 L29,26 L33,26 L33,22 L35,22 L35,26 L39,26 L39,22 L41,22 L41,26 L44,26 L44,22 L46,22 L46,26 L50,26 L50,22 L52,22 L52,26 L52.136,26 C53.164,26 54,26.836 54,27.864 L54,28 Z M41,65.876 C41,65.944 40.944,66 40.876,66 L14.124,66 C14.056,66 14,65.944 14,65.876 L14,39.124 C14,39.056 14.056,39 14.124,39 L20,39 L20,37 L14.124,37 C12.953,37 12,37.953 12,39.124 L12,65.876 C12,67.047 12.953,68 14.124,68 L40.876,68 C42.047,68 43,67.047 43,65.876 L43,61 L41,61 L41,65.876 Z M68,14.124 L68,40.876 C68,42.047 67.047,43 65.876,43 L60,43 L60,41 L65.876,41 C65.944,41 66,40.944 66,40.876 L66,14.124 C66,14.056 65.944,14 65.876,14 L39.124,14 C39.056,14 39,14.056 39,14.124 L39,20 L37,20 L37,14.124 C37,12.953 37.953,12 39.124,12 L65.876,12 C67.047,12 68,12.953 68,14.124 L68,14.124 Z" id="Amazon-EC2_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'S3 Bucket': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <title>Icon-Architecture/64/Arch_Amazon-Simple-Storage-Service_64</title>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#1B660F" offset="0%"></stop>
            <stop stop-color="#6CAE3E" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Amazon-Simple-Storage-Service_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Rectangle" fill="url(#linearGradient-1)">
            <rect x="0" y="0" width="80" height="80"></rect>
        </g>
        <g id="Icon-Service/64/Amazon-Simple-Storage-Service_64" transform="translate(8.000000, 8.000000)" fill="#FFFFFF">
            <path d="M52.8359,34.8926 L53.2199,32.1886 C56.7609,34.3096 56.8069,35.1856 56.8059132,35.2096 C56.7999,35.2146 56.1959,35.7186 52.8359,34.8926 L52.8359,34.8926 Z M50.8929,34.3526 C44.7729,32.5006 36.2499,28.5906 32.8009,26.9606 C32.8009,26.9466 32.8049,26.9336 32.8049,26.9196 C32.8049,25.5946 31.7269,24.5166 30.4009,24.5166 C29.0769,24.5166 27.9989,25.5946 27.9989,26.9196 C27.9989,28.2446 29.0769,29.3226 30.4009,29.3226 C30.9829,29.3226 31.5109,29.1056 31.9279,28.7606 C35.9859,30.6816 44.4429,34.5346 50.6079,36.3546 L48.1699,53.5606 C48.1629,53.6076 48.1599,53.6546 48.1599,53.7016 C48.1599,55.2166 41.4529,57.9996 30.4939,57.9996 C19.4189,57.9996 12.6409,55.2166 12.6409,53.7016 C12.6409,53.6556 12.6379,53.6106 12.6319,53.5656 L7.5379,16.3586 C11.9469,19.3936 21.4299,20.9996 30.4999,20.9996 C39.5559,20.9996 49.0229,19.3996 53.4409,16.3736 L50.8929,34.3526 Z M6.9999,12.4776 C7.0719,11.1616 14.6339,5.9996 30.4999,5.9996 C46.3639,5.9996 53.9269,11.1606 53.9999,12.4776 L53.9999,12.9266 C53.1299,15.8776 43.3299,18.9996 30.4999,18.9996 C17.6479,18.9996 7.8429,15.8676 6.9999,12.9126 L6.9999,12.4776 Z M55.9999,12.4996 C55.9999,9.0346 46.0659,3.9996 30.4999,3.9996 C14.9339,3.9996 4.9999,9.0346 4.9999,12.4996 L5.0939,13.2536 L10.6419,53.7776 C10.7749,58.3096 22.8609,59.9996 30.4939,59.9996 C39.9659,59.9996 50.0289,57.8216 50.1589,53.7806 L52.5549,36.8836 C53.8879,37.2026 54.9849,37.3656 55.8659,37.3656 C57.0489,37.3656 57.8489,37.0766 58.3339,36.4986 C58.7319,36.0246 58.8839,35.4506 58.7699,34.8396 C58.5109,33.4556 56.8679,31.9636 53.5219,30.0546 L55.8979,13.2926 L55.9999,12.4996 Z" id="Amazon-Simple-Storage-Service-Icon_64_Squid"></path>
        </g>
    </g>
</svg>'''),
        'RDS Instance': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_Amazon-RDS_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#2E27AD" offset="0%"></stop>
            <stop stop-color="#527FFF" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Amazon-RDS_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Database" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M15.414,14 L24.707,23.293 L23.293,24.707 L14,15.414 L14,23 L12,23 L12,13 C12,12.448 12.447,12 13,12 L23,12 L23,14 L15.414,14 Z M68,13 L68,23 L66,23 L66,15.414 L56.707,24.707 L55.293,23.293 L64.586,14 L57,14 L57,12 L67,12 C67.553,12 68,12.448 68,13 L68,13 Z M66,57 L68,57 L68,67 C68,67.552 67.553,68 67,68 L57,68 L57,66 L64.586,66 L55.293,56.707 L56.707,55.293 L66,64.586 L66,57 Z M65.5,39.213 C65.5,35.894 61.668,32.615 55.25,30.442 L55.891,28.548 C63.268,31.045 67.5,34.932 67.5,39.213 C67.5,43.495 63.268,47.383 55.89,49.879 L55.249,47.984 C61.668,45.812 65.5,42.534 65.5,39.213 L65.5,39.213 Z M14.556,39.213 C14.556,42.393 18.143,45.585 24.152,47.753 L23.473,49.634 C16.535,47.131 12.556,43.333 12.556,39.213 C12.556,35.094 16.535,31.296 23.473,28.792 L24.152,30.673 C18.143,32.842 14.556,36.034 14.556,39.213 L14.556,39.213 Z M24.707,56.707 L15.414,66 L23,66 L23,68 L13,68 C12.447,68 12,67.552 12,67 L12,57 L14,57 L14,64.586 L23.293,55.293 L24.707,56.707 Z M40,31.286 C32.854,31.286 29,29.44 29,28.686 C29,27.931 32.854,26.086 40,26.086 C47.145,26.086 51,27.931 51,28.686 C51,29.44 47.145,31.286 40,31.286 L40,31.286 Z M40.029,39.031 C33.187,39.031 29,37.162 29,36.145 L29,31.284 C31.463,32.643 35.832,33.286 40,33.286 C44.168,33.286 48.537,32.643 51,31.284 L51,36.145 C51,37.163 46.835,39.031 40.029,39.031 L40.029,39.031 Z M40.029,46.667 C33.187,46.667 29,44.798 29,43.781 L29,38.862 C31.431,40.291 35.742,41.031 40.029,41.031 C44.292,41.031 48.578,40.292 51,38.867 L51,43.781 C51,44.799 46.835,46.667 40.029,46.667 L40.029,46.667 Z M40,53.518 C32.883,53.518 29,51.605 29,50.622 L29,46.498 C31.431,47.927 35.742,48.667 40.029,48.667 C44.292,48.667 48.578,47.929 51,46.503 L51,50.622 C51,51.605 47.117,53.518 40,53.518 L40,53.518 Z M40,24.086 C33.739,24.086 27,25.525 27,28.686 L27,50.622 C27,53.836 33.54,55.518 40,55.518 C46.46,55.518 53,53.836 53,50.622 L53,28.686 C53,25.525 46.261,24.086 40,24.086 L40,24.086 Z" id="Amazon-RDS_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'Lambda Function': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_AWS-Lambda_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#C8511B" offset="0%"></stop>
            <stop stop-color="#FF9900" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_AWS-Lambda_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Compute" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M28.0075352,66 L15.5907274,66 L29.3235885,37.296 L35.5460249,50.106 L28.0075352,66 Z M30.2196674,34.553 C30.0512768,34.208 29.7004629,33.989 29.3175745,33.989 L29.3145676,33.989 C28.9286723,33.99 28.5778583,34.211 28.4124746,34.558 L13.097944,66.569 C12.9495999,66.879 12.9706487,67.243 13.1550766,67.534 C13.3374998,67.824 13.6582439,68 14.0020416,68 L28.6420072,68 C29.0299071,68 29.3817234,67.777 29.5481094,67.428 L37.563706,50.528 C37.693006,50.254 37.6920037,49.937 37.5586944,49.665 L30.2196674,34.553 Z M64.9953491,66 L52.6587274,66 L32.866809,24.57 C32.7014253,24.222 32.3486067,24 31.9617091,24 L23.8899822,24 L23.8990031,14 L39.7197081,14 L59.4204149,55.429 C59.5857986,55.777 59.9386172,56 60.3255148,56 L64.9953491,56 L64.9953491,66 Z M65.9976745,54 L60.9599868,54 L41.25928,12.571 C41.0938963,12.223 40.7410777,12 40.3531778,12 L22.89768,12 C22.3453987,12 21.8963569,12.447 21.8953545,12.999 L21.884329,24.999 C21.884329,25.265 21.9885708,25.519 22.1780103,25.707 C22.3654452,25.895 22.6200358,26 22.8866544,26 L31.3292417,26 L51.1221625,67.43 C51.2885485,67.778 51.6393624,68 52.02626,68 L65.9976745,68 C66.5519605,68 67,67.552 67,67 L67,55 C67,54.448 66.5519605,54 65.9976745,54 L65.9976745,54 Z" id="AWS-Lambda_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'Security Group': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_AWS-Shield_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#BD0816" offset="0%"></stop>
            <stop stop-color="#FF5252" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_AWS-Shield_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Security-Identity-Compliance" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M54.0106622,49.9995 L52.0106622,49.9995 L52.0106622,53.9995 L48.0106622,53.9995 L48.0106622,55.9995 L52.0106622,55.9995 L52.0106622,59.9995 L54.0106622,59.9995 L54.0106622,55.9995 L58.0106622,55.9995 L58.0106622,53.9995 L54.0106622,53.9995 L54.0106622,49.9995 Z M61.0106622,54.9995 C61.0106622,50.5885 57.4216622,46.9995 53.0106622,46.9995 C48.5996622,46.9995 45.0106622,50.5885 45.0106622,54.9995 C45.0106622,59.4105 48.5996622,62.9995 53.0106622,62.9995 C57.4216622,62.9995 61.0106622,59.4105 61.0106622,54.9995 L61.0106622,54.9995 Z M63.0106622,54.9995 C63.0106622,60.5135 58.5246622,64.9995 53.0106622,64.9995 C47.4966622,64.9995 43.0106622,60.5135 43.0106622,54.9995 C43.0106622,49.4855 47.4966622,44.9995 53.0106622,44.9995 C58.5246622,44.9995 63.0106622,49.4855 63.0106622,54.9995 L63.0106622,54.9995 Z M36.0106622,57.9705 L36.0106622,22.4555 L25.0106622,26.6865 L25.0106622,46.9995 C25.0226622,47.4135 25.4066622,57.3795 36.0106622,57.9705 L36.0106622,57.9705 Z M49.0106622,43.6995 L49.0106622,26.6865 L38.0106622,22.4555 L38.0106622,57.9625 C39.1706622,57.8855 40.2476622,57.6805 41.2466622,57.3635 C41.3816622,58.0325 41.5806622,58.6775 41.8216622,59.3015 C40.3566622,59.7605 38.7516622,59.9995 37.0106622,59.9995 C23.4516622,59.9995 23.0136622,47.1515 23.0106622,47.0215 L23.0106622,25.9995 C23.0106622,25.5855 23.2656622,25.2145 23.6516622,25.0655 L36.6516622,20.0655 C36.8836622,19.9775 37.1376622,19.9775 37.3696622,20.0655 L50.3696622,25.0655 C50.7556622,25.2145 51.0106622,25.5855 51.0106622,25.9995 L51.0106622,43.1805 C50.3226622,43.2965 49.6546622,43.4715 49.0106622,43.6995 L49.0106622,43.6995 Z M44.7556622,63.6875 C45.3136622,64.2165 45.9206622,64.6925 46.5726622,65.1085 C43.8176622,66.3565 40.6146622,66.9875 37.0106622,66.9875 C30.6836622,66.9875 25.6396622,65.0625 22.0196622,61.2665 C15.5886622,54.5235 15.9906622,44.3805 16.0116622,43.9525 L16.0106622,21.9995 C16.0106622,21.5905 16.2596622,21.2235 16.6396622,21.0705 L36.6396622,13.0705 C36.8776622,12.9765 37.1436622,12.9765 37.3816622,13.0705 L57.3816622,21.0705 C57.7616622,21.2235 58.0106622,21.5905 58.0106622,21.9995 L58.0106622,43.9995 C58.0106622,43.9995 58.0126622,44.0435 58.0146622,44.1065 C57.3746622,43.8115 56.7056622,43.5745 56.0116622,43.3945 L56.0106622,22.6765 L37.0106622,15.0765 L18.0106622,22.6765 L18.0106622,43.9995 C18.0046622,44.1425 17.6356622,53.7835 23.4766622,59.8965 C26.7036622,63.2745 31.2576622,64.9875 37.0106622,64.9875 C39.8986622,64.9875 42.4856622,64.5455 44.7556622,63.6875 L44.7556622,63.6875 Z" id="AWS-Shield_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'VPC': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_Amazon-Virtual-Private-Cloud_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#4D27A8" offset="0%"></stop>
            <stop stop-color="#A166FF" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Amazon-Virtual-Private-Cloud_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Networking-Content-Delivery" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M61,41.3717025 L55.5,39.1717025 L55.5,59.1227025 C57.106,58.9627025 58.401,58.4347025 59.321,57.5007025 C61.021,55.7727025 61.001,53.2397025 61,53.2147025 L61,41.3717025 Z M53.5,59.1357025 L53.5,39.1717025 L48,41.3717025 L48,53.1947025 C48.007,53.4017025 48.234,58.5517025 53.5,59.1357025 L53.5,59.1357025 Z M63,53.1947025 C63.003,53.3077025 63.053,56.5417025 60.765,58.8847025 C59.269,60.4177025 57.16,61.1947025 54.5,61.1947025 C47.927,61.1947025 46.065,55.9767025 46,53.2187025 L46,40.6947025 C46,40.2857025 46.249,39.9177025 46.629,39.7657025 L54.129,36.7657025 C54.367,36.6707025 54.633,36.6707025 54.871,36.7657025 L62.371,39.7657025 C62.751,39.9177025 63,40.2857025 63,40.6947025 L63,53.1947025 Z M66.001,51.2287025 L66,37.8717025 L54.5,33.2717025 L43,37.8717025 L43,51.1947025 C42.998,51.2857025 42.865,57.4227025 46.534,61.1987025 C48.466,63.1867025 51.146,64.1947025 54.5,64.1947025 C57.877,64.1947025 60.57,63.1797025 62.504,61.1787025 C66.168,57.3867025 66.003,51.2897025 66.001,51.2287025 L66.001,51.2287025 Z M63.942,62.5677025 C61.617,64.9747025 58.44,66.1947025 54.5,66.1947025 C50.579,66.1947025 47.413,64.9787025 45.09,62.5807025 C40.831,58.1877025 40.991,51.4477025 41,51.1637025 L41,37.1947025 C41,36.7857025 41.249,36.4177025 41.629,36.2657025 L54.129,31.2657025 C54.367,31.1707025 54.633,31.1707025 54.871,31.2657025 L67.371,36.2657025 C67.751,36.4177025 68,36.7857025 68,37.1947025 L68,51.1947025 C68.009,51.4447025 68.189,58.1727025 63.942,62.5677025 L63.942,62.5677025 Z M23.055,47.1947025 L38,47.1947025 L38,49.1947025 L23.055,49.1947025 C16.977,49.1947025 12.337,45.1427025 12.024,39.5597025 C12.002,39.3317025 12,39.0657025 12,38.7997025 C12,31.9307025 16.803,29.4017025 19.604,28.5117025 C19.584,28.1907025 19.574,27.8657025 19.574,27.5387025 C19.574,22.0857025 23.464,16.3807025 28.621,14.2687025 C34.677,11.7887025 41.062,12.9897025 45.695,17.4757025 C47.256,18.9967025 48.446,20.6207025 49.307,22.4097025 C50.513,21.3747025 51.969,20.8187025 53.529,20.8187025 C56.834,20.8187025 60.33,23.4127025 60.931,28.3817025 C63.114,28.9317025 65.854,30.0997025 67.788,32.5797025 L66.212,33.8097025 C64.43,31.5237025 61.741,30.5717025 59.8,30.1737025 C59.355,30.0837025 59.028,29.7057025 59.002,29.2537025 C58.741,24.8327025 55.982,22.8187025 53.529,22.8187025 C52.067,22.8187025 50.771,23.5087025 49.78,24.8137025 C49.559,25.1057025 49.199,25.2567025 48.835,25.1987025 C48.474,25.1437025 48.17,24.8967025 48.045,24.5537025 C47.278,22.4637025 46.054,20.6177025 44.302,18.9107025 C40.258,14.9967025 34.676,13.9517025 29.379,16.1197025 C24.93,17.9417025 21.574,22.8507025 21.574,27.5387025 C21.574,28.0797025 21.605,28.6147025 21.668,29.1277025 C21.729,29.6287025 21.405,30.0967025 20.915,30.2187025 C18.333,30.8577025 14,32.8237025 14,38.7997025 C14,39.0017025 13.998,39.2047025 14.018,39.4077025 C14.272,43.9357025 18.072,47.1947025 23.055,47.1947025 L23.055,47.1947025 Z" id="Amazon-Virtual-Private-Cloud_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>'''),
        'Elastic Load Balancer': svg_to_data_url('''<?xml version="1.0" encoding="UTF-8"?>
<svg width="80px" height="80px" viewBox="0 0 80 80" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <!-- Generator: Sketch 64 (93537) - https://sketch.com -->
    <title>Icon-Architecture/64/Arch_Elastic-Load-Balancing_64</title>
    <desc>Created with Sketch.</desc>
    <defs>
        <linearGradient x1="0%" y1="100%" x2="100%" y2="0%" id="linearGradient-1">
            <stop stop-color="#4D27A8" offset="0%"></stop>
            <stop stop-color="#A166FF" offset="100%"></stop>
        </linearGradient>
    </defs>
    <g id="Icon-Architecture/64/Arch_Elastic-Load-Balancing_64" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <g id="Icon-Architecture-BG/64/Networking-Content-Delivery" fill="url(#linearGradient-1)">
            <rect id="Rectangle" x="0" y="0" width="80" height="80"></rect>
        </g>
        <path d="M30,53 C22.832,53 17,47.168 17,40 C17,32.832 22.832,27 30,27 C37.168,27 43,32.832 43,40 C43,47.168 37.168,53 30,53 M60,59 C60,61.206 58.206,63 56,63 C53.794,63 52,61.206 52,59 C52,56.794 53.794,55 56,55 C58.206,55 60,56.794 60,59 M56,17 C58.206,17 60,18.794 60,21 C60,23.206 58.206,25 56,25 C53.794,25 52,23.206 52,21 C52,18.794 53.794,17 56,17 M59,36 C61.206,36 63,37.794 63,40 C63,42.206 61.206,44 59,44 C56.794,44 55,42.206 55,40 C55,37.794 56.794,36 59,36 M44.949,41 L53.09,41 C53.568,43.833 56.033,46 59,46 C62.309,46 65,43.309 65,40 C65,36.691 62.309,34 59,34 C56.033,34 53.568,36.167 53.09,39 L44.949,39 C44.823,37.099 44.344,35.297 43.572,33.654 L52.446,25.823 C53.442,26.559 54.669,27 56,27 C59.309,27 62,24.309 62,21 C62,17.691 59.309,15 56,15 C52.691,15 50,17.691 50,21 C50,22.256 50.389,23.421 51.051,24.386 L42.581,31.859 C39.904,27.738 35.271,25 30,25 C21.729,25 15,31.729 15,40 C15,48.271 21.729,55 30,55 C35.271,55 39.904,52.262 42.581,48.141 L51.051,55.614 C50.389,56.579 50,57.744 50,59 C50,62.309 52.691,65 56,65 C59.309,65 62,62.309 62,59 C62,55.691 59.309,53 56,53 C54.669,53 53.442,53.441 52.446,54.177 L43.572,46.346 C44.344,44.703 44.823,42.901 44.949,41" id="Elastic-Load-Balancing_Icon_64_Squid" fill="#FFFFFF"></path>
    </g>
</svg>''')
    }
    
    # Return the appropriate icon URL or a default AWS icon
    return icon_mapping.get(resource_type, "https://d1.awsstatic.com/webteam/architecture-icons/q42023/Res_AWS-Logo_48.svg")


def get_resource_info(event_detail):
    """Extract resource information based on the event type."""
    
    # NOTE: IAM User and Route53 DNS Record resources are now handled by global notifiers
    # (resource_creation_notifier_global.py and resource_deletion_notifier_global.py)
    # since these are global AWS resources not tied to a specific region.
    
    event_source = event_detail.get('eventSource', '')
    event_name = event_detail.get('eventName', '')
    
    # Default resource info structure
    resource_info = {
        'resourceType': 'Unknown',
        'resourceName': 'Unknown',
        'resourceId': 'Unknown',
        'additionalInfo': {}
    }
    
    # EC2 Instance Deletion
    if event_source == 'ec2.amazonaws.com' and event_name == 'TerminateInstances':
        instance_ids = event_detail.get('requestParameters', {}).get('instancesSet', {}).get('items', [])
        if instance_ids:
            instance_id = instance_ids[0].get('instanceId')
            instance_name = None
            tags = {}
            
            # Try to get instance name and tags from EC2 API
            # Note: For termination events, the instance might already be deleted,
            # so it's possible we can't retrieve the name
            try:
                response = ec2_client.describe_tags(
                    Filters=[
                        {
                            'Name': 'resource-id',
                            'Values': [instance_id]
                        }
                    ]
                )
                
                for tag in response.get('Tags', []):
                    if tag.get('Key') == 'Name':
                        instance_name = tag.get('Value')
                    tags[tag.get('Key')] = tag.get('Value')
                    
            except Exception as e:
                logger.warning(f"Error getting instance tags for {instance_id}: {str(e)}")
            
            # Default to instance ID if name not found
            if not instance_name:
                instance_name = instance_id
                
            resource_info = {
                'resourceType': 'EC2 Instance',
                'resourceName': instance_name,
                'resourceId': instance_id,
                'additionalInfo': {
                    'region': event_detail.get('awsRegion', 'Unknown'),
                    'tags': tags if tags else 'No tags found'
                }
            }
    
    # S3 Bucket Deletion
    elif event_source == 's3.amazonaws.com' and event_name == 'DeleteBucket':
        bucket_name = event_detail.get('requestParameters', {}).get('bucketName')
        tags = {}
        
        # Try to get bucket tags
        # Note: Bucket might already be deleted
        try:
            response = s3_client.get_bucket_tagging(
                Bucket=bucket_name
            )
            tag_set = response.get('TagSet', [])
            for tag in tag_set:
                tags[tag.get('Key')] = tag.get('Value')
        except Exception as e:
            logger.warning(f"Error getting bucket tags for {bucket_name}: {str(e)}")
            
        resource_info = {
            'resourceType': 'S3 Bucket',
            'resourceName': bucket_name,
            'resourceId': bucket_name,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'tags': tags if tags else 'No tags found or bucket already deleted'
            }
        }
    
    # RDS Instance Deletion
    elif event_source == 'rds.amazonaws.com' and event_name == 'DeleteDBInstance':
        request_params = event_detail.get('requestParameters', {})
        db_instance_id = request_params.get('dBInstanceIdentifier')
        tags = {}
        
        # Try to get RDS instance tags
        try:
            response = rds_client.list_tags_for_resource(
                ResourceName=f"arn:aws:rds:{event_detail.get('awsRegion', 'us-east-1')}:{event_detail.get('userIdentity', {}).get('accountId', '')}:db:{db_instance_id}"
            )
            for tag in response.get('TagList', []):
                tags[tag.get('Key')] = tag.get('Value')
        except Exception as e:
            logger.warning(f"Error getting RDS instance tags for {db_instance_id}: {str(e)}")
            
        resource_info = {
            'resourceType': 'RDS Instance',
            'resourceName': db_instance_id,
            'resourceId': db_instance_id,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'skipFinalSnapshot': request_params.get('skipFinalSnapshot', 'Unknown'),
                'tags': tags if tags else 'No tags found or instance already deleted'
            }
        }
    
    # Lambda Function Deletion
    elif event_source == 'lambda.amazonaws.com' and event_name == 'DeleteFunction20150331':
        request_params = event_detail.get('requestParameters', {})
        function_name = request_params.get('functionName')
        tags = {}
        
        # Try to get Lambda function tags
        try:
            response = lambda_client.list_tags(
                Resource=f"arn:aws:lambda:{event_detail.get('awsRegion', 'us-east-1')}:{event_detail.get('userIdentity', {}).get('accountId', '')}:function:{function_name}"
            )
            tags = response.get('Tags', {})
        except Exception as e:
            logger.warning(f"Error getting Lambda function tags for {function_name}: {str(e)}")
            
        resource_info = {
            'resourceType': 'Lambda Function',
            'resourceName': function_name,
            'resourceId': function_name,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'tags': tags if tags else 'No tags found or function already deleted'
            }
        }
    
    # Security Group Deletion
    elif event_source == 'ec2.amazonaws.com' and event_name == 'DeleteSecurityGroup':
        request_params = event_detail.get('requestParameters', {})
        group_name = request_params.get('groupName')
        group_id = request_params.get('groupId')
        tags = {}
        
        # Try to get security group tags
        try:
            response = ec2_client.describe_tags(
                Filters=[
                    {
                        'Name': 'resource-id',
                        'Values': [group_id]
                    }
                ]
            )
            for tag in response.get('Tags', []):
                tags[tag.get('Key')] = tag.get('Value')
        except Exception as e:
            logger.warning(f"Error getting security group tags for {group_id}: {str(e)}")
            
        resource_info = {
            'resourceType': 'Security Group',
            'resourceName': group_name,
            'resourceId': group_id,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'tags': tags if tags else 'No tags found or security group already deleted'
            }
        }
    
    # VPC Deletion
    elif event_source == 'ec2.amazonaws.com' and event_name == 'DeleteVpc':
        request_params = event_detail.get('requestParameters', {})
        vpc_id = request_params.get('vpcId')
        tags = {}
        
        # Try to get VPC tags
        try:
            response = ec2_client.describe_tags(
                Filters=[
                    {
                        'Name': 'resource-id',
                        'Values': [vpc_id]
                    }
                ]
            )
            for tag in response.get('Tags', []):
                tags[tag.get('Key')] = tag.get('Value')
        except Exception as e:
            logger.warning(f"Error getting VPC tags for {vpc_id}: {str(e)}")
            
        resource_info = {
            'resourceType': 'VPC',
            'resourceName': vpc_id,
            'resourceId': vpc_id,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'tags': tags if tags else 'No tags found or VPC already deleted'
            }
        }
    
    # Elastic Load Balancer Deletion
    elif event_source == 'elasticloadbalancing.amazonaws.com' and event_name == 'DeleteLoadBalancer':
        request_params = event_detail.get('requestParameters', {})
        lb_arn = request_params.get('loadBalancerArn')
        tags = {}
        
        # Extract the load balancer name from the ARN
        # Format: "arn:aws:elasticloadbalancing:region:account-id:loadbalancer/type/name/id"
        lb_name = "Unknown"
        if lb_arn:
            try:
                # Parse the ARN to get the load balancer name
                arn_parts = lb_arn.split('/')
                if len(arn_parts) >= 3:
                    lb_type = arn_parts[1]  # app, net, gateway, etc.
                    lb_name = arn_parts[2]   # The actual name
            except Exception as e:
                logger.warning(f"Error parsing load balancer ARN {lb_arn}: {str(e)}")
        
        # Try to get ELB tags
        try:
            if lb_arn:
                response = elb_client.describe_tags(
                    ResourceArns=[lb_arn]
                )
                tag_descriptions = response.get('TagDescriptions', [])
                if tag_descriptions:
                    for tag in tag_descriptions[0].get('Tags', []):
                        tags[tag.get('Key')] = tag.get('Value')
        except Exception as e:
            logger.warning(f"Error getting ELB tags for {lb_arn}: {str(e)}")
            
        resource_info = {
            'resourceType': 'Elastic Load Balancer',
            'resourceName': lb_name,
            'resourceId': lb_arn,
            'additionalInfo': {
                'region': event_detail.get('awsRegion', 'Unknown'),
                'loadBalancerType': lb_type if 'lb_type' in locals() else 'Unknown',
                'tags': tags if tags else 'No tags found or load balancer already deleted'
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