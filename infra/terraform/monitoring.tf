# Terraform configuration for monitoring infrastructure

resource "aws_cloudwatch_log_group" "energy_cost_logs" {
  name              = "/aws/ecs/energy-cost"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = "energy-cost-system"
  }
}

resource "aws_cloudwatch_dashboard" "energy_cost_dashboard" {
  dashboard_name = "energy-cost-system-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "energy-cost-api"],
            [".", "MemoryUtilization", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Service Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.postgres.id],
            [".", "CPUUtilization", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Metrics"
          period  = 300
        }
      }
    ]
  })
}

# SNS topic for alerts
resource "aws_sns_topic" "energy_cost_alerts" {
  name = "energy-cost-alerts-${var.environment}"

  tags = {
    Environment = var.environment
    Project     = "energy-cost-system"
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.energy_cost_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "energy-cost-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.energy_cost_alerts.arn]

  dimensions = {
    ServiceName = "energy-cost-api"
  }

  tags = {
    Environment = var.environment
    Project     = "energy-cost-system"
  }
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "energy-cost-high-db-connections-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.energy_cost_alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = {
    Environment = var.environment
    Project     = "energy-cost-system"
  }
}
