# Setting Up Microsoft Teams Webhook

This guide explains how to create a webhook URL in Microsoft Teams to receive AWS resource creation and deletion notifications.

## Steps to Create a Teams Webhook

1. **Open Microsoft Teams** and navigate to the team/channel where you want to receive notifications.

2. **Access Channel Settings**:
   - Click on the three dots (`...`) next to the channel name.
   - Select `Manage Channel` from the dropdown menu.

3. **Add a Connector**:
   - Click on the `Connectors` button.
   - In the Connectors list, search for `Incoming Webhook`.
   - Click `Configure` next to the Incoming Webhook option.

4. **Configure the Webhook**:
   - Provide a name for your webhook (e.g., "AWS Resource Notifier").
   - Optionally, upload an image for the webhook (AWS logo recommended).
   - Click `Create`.

5. **Copy the Webhook URL**:
   - After creation, a webhook URL will be generated.
   - **Important**: Copy this URL and keep it secure. It will be needed during the deployment of the AWS Resource Notifier.

6. **Complete Setup**:
   - Click `Done` to finish the webhook configuration.

## Using the Webhook URL

During deployment of the AWS Resource Notifier, you will need to provide this webhook URL in one of the following ways:

### Using the Deployment Script

The easiest way is to provide the webhook URL via the deployment script:

```bash
./deploy.sh --webhook-url "https://your-teams-webhook-url"
```

This will automatically deploy both the global and regional resource monitoring stacks with the provided webhook URL.

### Modifying CloudFormation Parameters

If you prefer to prepare your deployment parameters before running the script, you can update the `parameters.json` file:

```json
[
  {
    "ParameterKey": "TeamsWebhookUrl",
    "ParameterValue": "https://your-teams-webhook-url"
  }
]
```

### Manual Configuration

If you prefer not to include the webhook URL in your deployment files, you can update it manually in AWS Secrets Manager after deployment:

1. Log in to the AWS Management Console
2. Navigate to AWS Secrets Manager
3. Find the two secrets created by the deployment:
   - `<resource-prefix>-teams-webhook` (for regional resources)
   - `<resource-prefix>-global-teams-webhook` (for global resources)
4. Update each secret value with the following JSON structure:
   ```json
   {
     "webhookUrl": "https://your-teams-webhook-url"
   }
   ```

## Testing the Webhook

After deployment, you can test the webhook by:

1. **Creating a new AWS resource**: Create an EC2 instance, S3 bucket, etc. to test creation notifications.
2. **Deleting an AWS resource**: Delete a previously created resource to test deletion notifications.

Notifications should appear in the Microsoft Teams channel within a few seconds of the resource operation. Each notification will include:

- The resource type with its AWS service icon
- Resource details like name, ID, region
- The user who performed the action
- Additional metadata specific to the resource type
- Links to the AWS Management Console

## Troubleshooting

If notifications aren't appearing in Teams:

1. **Check the CloudWatch Logs**: Examine the logs for the Lambda functions to see if there are any errors.
2. **Verify the webhook URL**: Ensure the webhook URL is correct and still active in Teams.
3. **Check CloudTrail**: Confirm that the resource creation/deletion events are being recorded in CloudTrail.
4. **Test EventBridge Rules**: Use the AWS Management Console to verify the EventBridge rules are triggered.
5. **Check Lambda Permissions**: Ensure the Lambda functions have the necessary permissions to access Secrets Manager and call the webhook URL. 