import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Activity, Server, BarChart3, AlertTriangle, ArrowRight, Shield, Zap, Database } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">OpenMonitor</h1>
                <p className="text-sm text-muted-foreground">Open-source monitoring and observability platform</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-green-400 border-green-400">
                All Systems Operational
              </Badge>
              <Link href="/dashboard">
                <Button>
                  Launch Dashboard
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">Complete Observability Stack</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Monitor infrastructure, applications, and services with real-time metrics, distributed tracing, log
            aggregation, and intelligent alerting.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Card className="hover:shadow-lg transition-shadow border-primary/20">
            <CardHeader>
              <Server className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Infrastructure Monitoring</CardTitle>
              <CardDescription>
                Real-time monitoring of servers, containers, networks, and cloud resources
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <Activity className="h-8 w-8 text-secondary mb-2" />
              <CardTitle>Application Performance</CardTitle>
              <CardDescription>APM with distributed tracing, performance profiling, and error tracking</CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <Database className="h-8 w-8 text-chart-3 mb-2" />
              <CardTitle>Log Aggregation</CardTitle>
              <CardDescription>
                Centralized log collection, parsing, and search across all your services
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <AlertTriangle className="h-8 w-8 text-destructive mb-2" />
              <CardTitle>Intelligent Alerting</CardTitle>
              <CardDescription>
                Smart alerts with anomaly detection, escalation policies, and integrations
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* System Status Dashboard */}
        <Card className="mb-8 bg-gradient-to-r from-card to-muted/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              System Overview
            </CardTitle>
            <CardDescription>Real-time infrastructure and service health</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
                <div>
                  <span className="font-medium">Hosts Monitored</span>
                  <p className="text-2xl font-bold text-primary">247</p>
                </div>
                <Badge variant="outline" className="text-green-400 border-green-400">
                  Healthy
                </Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
                <div>
                  <span className="font-medium">Services</span>
                  <p className="text-2xl font-bold text-secondary">1,432</p>
                </div>
                <Badge variant="outline" className="text-green-400 border-green-400">
                  Running
                </Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
                <div>
                  <span className="font-medium">Active Alerts</span>
                  <p className="text-2xl font-bold text-destructive">3</p>
                </div>
                <Badge variant="outline" className="text-yellow-400 border-yellow-400">
                  Warning
                </Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
                <div>
                  <span className="font-medium">Data Ingested</span>
                  <p className="text-2xl font-bold text-chart-3">2.4TB</p>
                </div>
                <Badge variant="outline" className="text-green-400 border-green-400">
                  Normal
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="text-center">
          <h3 className="text-2xl font-bold mb-6">Get Started</h3>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" className="min-w-48">
                <BarChart3 className="h-4 w-4 mr-2" />
                Open Dashboard
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="min-w-48 bg-transparent">
              <Shield className="h-4 w-4 mr-2" />
              View Alerts
            </Button>
            <Button size="lg" variant="outline" className="min-w-48 bg-transparent">
              <Zap className="h-4 w-4 mr-2" />
              System Health
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 bg-muted/30">
        <div className="container mx-auto px-6 py-8">
          <div className="text-center text-muted-foreground">
            <p className="font-medium">OpenMonitor - Open-source observability platform</p>
            <p className="text-sm mt-2">Real-time monitoring • Distributed tracing • Intelligent alerting</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
