"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from "recharts"
import { Zap, Battery, Sun, TrendingUp, Info, ExternalLink, Download } from "lucide-react"

// Mock data for LCOE rankings
const lcoeRankings = [
  {
    id: 1,
    name: "Tesla Solar Panels + Powerwall 3",
    manufacturer: "Tesla",
    type: "solar+storage",
    lcoe: 0.087,
    lcos: 0.142,
    confidence: 0.92,
    lastUpdated: "2024-01-15",
    citations: 12,
    region: "California",
    useCase: "residential",
  },
  {
    id: 2,
    name: "Enphase IQ8 + IQ Battery 5P",
    manufacturer: "Enphase",
    type: "solar+storage",
    lcoe: 0.094,
    lcos: 0.156,
    confidence: 0.89,
    lastUpdated: "2024-01-14",
    citations: 8,
    region: "California",
    useCase: "residential",
  },
  {
    id: 3,
    name: "Tesla Megapack 2XL",
    manufacturer: "Tesla",
    type: "storage",
    lcoe: null,
    lcos: 0.098,
    confidence: 0.95,
    lastUpdated: "2024-01-16",
    citations: 15,
    region: "Texas",
    useCase: "utility",
  },
  {
    id: 4,
    name: "BYD Blade Battery",
    manufacturer: "BYD",
    type: "storage",
    lcoe: null,
    lcos: 0.112,
    confidence: 0.87,
    lastUpdated: "2024-01-13",
    citations: 6,
    region: "Texas",
    useCase: "utility",
  },
]

const chartData = [
  { name: "Tesla Solar+PW3", lcoe: 8.7, lcos: 14.2 },
  { name: "Enphase IQ8+5P", lcoe: 9.4, lcos: 15.6 },
  { name: "Tesla Megapack", lcoe: null, lcos: 9.8 },
  { name: "BYD Blade", lcoe: null, lcos: 11.2 },
]

export default function DashboardPage() {
  const [selectedScenario, setSelectedScenario] = useState("residential-ca")
  const [systemSize, setSystemSize] = useState([10])
  const [selectedEntity, setSelectedEntity] = useState(null)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Energy Cost Dashboard</h1>
                <p className="text-sm text-muted-foreground">Tesla-focused LCOE/LCOS analysis</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-primary border-primary">
                Live Data
              </Badge>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <Tabs defaultValue="rankings" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="rankings">Rankings</TabsTrigger>
            <TabsTrigger value="scenarios">Scenario Builder</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
            <TabsTrigger value="ops">Operations</TabsTrigger>
          </TabsList>

          <TabsContent value="rankings" className="space-y-6">
            {/* Scenario Selector */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>LCOE/LCOS Rankings</CardTitle>
                    <CardDescription>Levelized costs ranked by scenario with confidence intervals</CardDescription>
                  </div>
                  <Select value={selectedScenario} onValueChange={setSelectedScenario}>
                    <SelectTrigger className="w-64">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="residential-ca">Residential - California</SelectItem>
                      <SelectItem value="residential-tx">Residential - Texas</SelectItem>
                      <SelectItem value="commercial-ca">Commercial - California</SelectItem>
                      <SelectItem value="utility-tx">Utility - Texas</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {lcoeRankings.map((item, index) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                      onClick={() => setSelectedEntity(item)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                          {index + 1}
                        </div>
                        <div className="flex items-center gap-2">
                          {item.manufacturer === "Tesla" ? (
                            <Zap className="h-5 w-5 text-primary" />
                          ) : item.type.includes("storage") ? (
                            <Battery className="h-5 w-5 text-muted-foreground" />
                          ) : (
                            <Sun className="h-5 w-5 text-muted-foreground" />
                          )}
                          <div>
                            <p className="font-medium">{item.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {item.manufacturer} • {item.region} • {item.useCase}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        {item.lcoe && (
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">LCOE</p>
                            <p className="font-bold">${(item.lcoe * 100).toFixed(1)}¢/kWh</p>
                          </div>
                        )}
                        {item.lcos && (
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">LCOS</p>
                            <p className="font-bold">${(item.lcos * 100).toFixed(1)}¢/kWh</p>
                          </div>
                        )}
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Confidence</p>
                          <p className="font-bold">{(item.confidence * 100).toFixed(0)}%</p>
                        </div>
                        <Sheet>
                          <SheetTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <Info className="h-4 w-4" />
                            </Button>
                          </SheetTrigger>
                          <SheetContent>
                            <SheetHeader>
                              <SheetTitle>{item.name}</SheetTitle>
                              <SheetDescription>Data provenance and citations</SheetDescription>
                            </SheetHeader>
                            <div className="mt-6 space-y-4">
                              <div>
                                <h4 className="font-medium mb-2">Key Metrics</h4>
                                <div className="space-y-2">
                                  {item.lcoe && (
                                    <div className="flex justify-between">
                                      <span>LCOE:</span>
                                      <span className="font-mono">${(item.lcoe * 100).toFixed(1)}¢/kWh</span>
                                    </div>
                                  )}
                                  {item.lcos && (
                                    <div className="flex justify-between">
                                      <span>LCOS:</span>
                                      <span className="font-mono">${(item.lcos * 100).toFixed(1)}¢/kWh</span>
                                    </div>
                                  )}
                                  <div className="flex justify-between">
                                    <span>Confidence:</span>
                                    <span className="font-mono">{(item.confidence * 100).toFixed(1)}%</span>
                                  </div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-medium mb-2">Data Sources ({item.citations})</h4>
                                <div className="space-y-2">
                                  <div className="flex items-center gap-2 text-sm">
                                    <ExternalLink className="h-3 w-3" />
                                    <span>Tesla Energy Datasheet (2024)</span>
                                  </div>
                                  <div className="flex items-center gap-2 text-sm">
                                    <ExternalLink className="h-3 w-3" />
                                    <span>NREL Cost Database</span>
                                  </div>
                                  <div className="flex items-center gap-2 text-sm">
                                    <ExternalLink className="h-3 w-3" />
                                    <span>DOE Energy Storage Report</span>
                                  </div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-medium mb-2">Last Updated</h4>
                                <p className="text-sm text-muted-foreground">{item.lastUpdated}</p>
                              </div>
                            </div>
                          </SheetContent>
                        </Sheet>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Cost Comparison</CardTitle>
                <CardDescription>LCOE and LCOS by technology</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    lcoe: { label: "LCOE", color: "hsl(var(--chart-1))" },
                    lcos: { label: "LCOS", color: "hsl(var(--chart-2))" },
                  }}
                  className="h-80"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" />
                      <YAxis label={{ value: "¢/kWh", angle: -90, position: "insideLeft" }} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="lcoe" fill="var(--color-lcoe)" name="LCOE" />
                      <Bar dataKey="lcos" fill="var(--color-lcos)" name="LCOS" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="scenarios" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Scenario Builder</CardTitle>
                <CardDescription>Create custom analysis scenarios with specific parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="region">Region</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select region" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="california">California</SelectItem>
                          <SelectItem value="texas">Texas</SelectItem>
                          <SelectItem value="florida">Florida</SelectItem>
                          <SelectItem value="new-york">New York</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="use-case">Use Case</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select use case" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="residential">Residential</SelectItem>
                          <SelectItem value="commercial">Commercial</SelectItem>
                          <SelectItem value="utility">Utility Scale</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>System Size: {systemSize[0]} kW</Label>
                      <Slider
                        value={systemSize}
                        onValueChange={setSystemSize}
                        max={100}
                        min={1}
                        step={1}
                        className="mt-2"
                      />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="discount-rate">Discount Rate (%)</Label>
                      <Input type="number" placeholder="7.5" />
                    </div>
                    <div>
                      <Label htmlFor="project-life">Project Life (years)</Label>
                      <Input type="number" placeholder="25" />
                    </div>
                    <div>
                      <Label htmlFor="degradation">Annual Degradation (%)</Label>
                      <Input type="number" placeholder="0.5" />
                    </div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button className="flex-1">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Run Analysis
                  </Button>
                  <Button variant="outline">Save Scenario</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="compare" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">Tesla Powerwall 3</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Capacity:</span>
                  <span className="font-mono">13.5 kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Power:</span>
                  <span className="font-mono">11.5 kW</span>
                </div>
                <div className="flex justify-between">
                  <span>LCOS:</span>
                  <span className="font-mono text-primary">14.2¢/kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Warranty:</span>
                  <span className="font-mono">10 years</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Battery className="h-5 w-5" />
                  <CardTitle className="text-lg">Enphase IQ Battery 5P</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Capacity:</span>
                  <span className="font-mono">5.0 kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Power:</span>
                  <span className="font-mono">3.84 kW</span>
                </div>
                <div className="flex justify-between">
                  <span>LCOS:</span>
                  <span className="font-mono">15.6¢/kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Warranty:</span>
                  <span className="font-mono">15 years</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Battery className="h-5 w-5" />
                  <CardTitle className="text-lg">LG Chem RESU</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Capacity:</span>
                  <span className="font-mono">9.8 kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Power:</span>
                  <span className="font-mono">5.0 kW</span>
                </div>
                <div className="flex justify-between">
                  <span>LCOS:</span>
                  <span className="font-mono">16.8¢/kWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Warranty:</span>
                  <span className="font-mono">10 years</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ops" className="space-y-6">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Pipeline Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-primary">Active</div>
                  <p className="text-sm text-muted-foreground">Last run: 2 hours ago</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Data Freshness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">94%</div>
                  <p className="text-sm text-muted-foreground">&lt; 90 days old</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Extraction Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">1,247</div>
                  <p className="text-sm text-muted-foreground">facts/hour</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Error Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">0.3%</div>
                  <p className="text-sm text-muted-foreground">Last 24h</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
