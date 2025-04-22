# AWS Resource Notifier - Architecture

The AWS Resource Notifier uses a serverless event-driven architecture to monitor AWS CloudTrail events and send notifications to Microsoft Teams when resources are created or deleted.

## System Architecture

The architecture is split into two main components:

1. **Regional Resource Monitoring**: Monitors resources specific to an AWS region
2. **Global Resource Monitoring**: Monitors AWS global resources from a single region

![Architecture Diagram](./architecture.png)

## Architecture Components

1. **CloudTrail**: Records API calls made in your AWS account
2. **EventBridge**: Filters CloudTrail events for specific resource creation and deletion events
3. **Lambda Functions**: Four specialized functions that process events and format notifications:
   - Regional Resource Creation Notifier
   - Regional Resource Deletion Notifier
   - Global Resource Creation Notifier
   - Global Resource Deletion Notifier
4. **Secrets Manager**: Securely stores the Microsoft Teams webhook URL
5. **Microsoft Teams**: Receives and displays notifications

## Architecture Flow

### Resource Creation Flow

1. A user creates a new AWS resource (EC2, S3, RDS, etc.)
2. CloudTrail logs the API call as an event
3. EventBridge rules filter for the specific resource creation event
4. When a matching event is detected, EventBridge triggers the appropriate Lambda function:
   - Regional resources → Regional Creation Notifier
   - Global resources → Global Creation Notifier
5. The Lambda function:
   - Extracts resource details from the event
   - Retrieves the Teams webhook URL from Secrets Manager
   - Formats a notification card for Teams with resource information
   - Sends the notification to the Teams channel via the webhook

### Resource Deletion Flow

1. A user deletes an AWS resource
2. CloudTrail logs the API call as an event
3. EventBridge rules filter for the specific resource deletion event
4. When a matching event is detected, EventBridge triggers the appropriate Lambda function:
   - Regional resources → Regional Deletion Notifier
   - Global resources → Global Deletion Notifier
5. The Lambda function:
   - Extracts resource details from the event
   - Retrieves the Teams webhook URL from Secrets Manager
   - Formats a notification card for Teams with deletion information
   - Sends the notification to the Teams channel via the webhook

## Monitored Resources

### Regional Resources
- EC2 Instances
- S3 Buckets
- RDS Instances
- Lambda Functions
- Security Groups
- VPCs
- Elastic Load Balancers (ALB/NLB)

### Global Resources
- IAM Users
- Route53 DNS Records

## Event Pattern Examples

Each resource type requires specific EventBridge rule patterns for creation and deletion events. Here are examples for both types:

### EC2 Instance

**Creation Event Pattern**:
```json
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": ["RunInstances"]
  }
}
```

**Deletion Event Pattern**:
```json
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": ["TerminateInstances"]
  }
}
```

### S3 Bucket

**Creation Event Pattern**:
```json
{
  "source": ["aws.s3"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["s3.amazonaws.com"],
    "eventName": ["CreateBucket"]
  }
}
```

**Deletion Event Pattern**:
```json
{
  "source": ["aws.s3"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["s3.amazonaws.com"],
    "eventName": ["DeleteBucket"]
  }
}
```

## Notification Format

The notifications are formatted as Microsoft Teams cards with a modern design:

### Creation Notifications
- Blue-themed card with creation details
- AWS service icon for the resource type
- Resource name, ID, and region
- Creation timestamp and user information
- Detailed resource metadata
- Links to the AWS Management Console

### Deletion Notifications
- Red-themed card with deletion details
- AWS service icon for the resource type
- Resource name, ID, and region
- Deletion timestamp and user information
- Detailed resource metadata
- Links to the AWS Management Console

## Deployment Model

The solution is deployed using CloudFormation in two parts:

1. **global-services.yaml**: Deploys the global resources monitoring stack
   - IAM User and Route53 event monitoring
   - Lambda functions for global resource notifications

2. **regional-services.yaml**: Deploys the regional resources monitoring stack
   - Regional resource event monitoring
   - Lambda functions for regional resource notifications

## Security Considerations

1. The Lambda functions have least-privilege permissions
2. The Microsoft Teams webhook URL is stored securely in AWS Secrets Manager
3. CloudTrail logs are encrypted
4. All communications use HTTPS
5. Region-specific monitoring to respect data sovereignty

## Scalability

This architecture scales automatically:
- EventBridge can handle thousands of events per second
- Lambda functions scale based on the number of incoming events
- Regional stacks can be deployed to multiple regions independently
- No infrastructure provisioning or management required

## Customization Points

The solution can be extended or customized by:

1. Adding new EventBridge rules to monitor additional resource types
2. Modifying the Lambda functions to extract and display different resource information
3. Updating the Teams message template to change the notification appearance
4. Implementing additional notification channels (e.g., Slack, Email, SNS)