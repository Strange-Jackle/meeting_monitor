import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Download,
  Settings,
  ArrowDown,
  ArrowUp
} from 'lucide-react';

const visitData = [
  { month: 'Mar \'21', visits: 4000 },
  { month: 'Apr \'21', visits: 3000 },
  { month: 'May \'21', visits: 2000 },
  { month: 'Jun \'21', visits: 2780 },
  { month: 'Jul \'21', visits: 1890 },
  { month: 'Aug \'21', visits: 2390 },
  { month: 'Sep \'21', visits: 3490 },
  { month: 'Oct \'21', visits: 3490 },
  { month: 'Nov \'21', visits: 3000 },
  { month: 'Dec \'21', visits: 2500 },
  { month: 'Jan \'22', visits: 2700 },
  { month: 'Feb \'22', visits: 3100 },
];

const sparklineData1 = [
  { value: 4000 }, { value: 3000 }, { value: 2000 }, { value: 2780 }, { value: 1890 }, { value: 2390 }, { value: 3490 }
];
const sparklineData2 = [
  { value: 2400 }, { value: 1398 }, { value: 9800 }, { value: 3908 }, { value: 4800 }, { value: 3800 }, { value: 4300 }
];
const sparklineData3 = [
  { value: 1000 }, { value: 2000 }, { value: 1500 }, { value: 3000 }, { value: 2000 }, { value: 4000 }, { value: 3200 }
];

const audienceData = [
  { name: 'Group A', value: 400 },
  { name: 'Group B', value: 300 },
];

const COLORS = ['#3b82f6', '#e2e8f0']; // Blue and Slate-200
const GENDER_COLORS = ['#2dd4bf', '#e2e8f0']; // Teal and Slate-200
const AGE_COLORS = ['#f97316', '#e2e8f0']; // Orange and Slate-200
const LANG_COLORS = ['#a855f7', '#e2e8f0']; // Purple and Slate-200

const AnalyticsView: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <span>Home</span> &gt; <span>Dashboards</span> &gt; <span className="text-gray-900 font-medium">Analytics & Insights</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Analytics dashboard</h1>
            <p className="text-gray-500">Monitor metrics, check reports and review performance</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 shadow-sm">
              <Settings size={16} /> Settings
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm">
              <Download size={16} /> Export
            </button>
          </div>
        </div>

        {/* Visitors Overview Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Visitors Overview</h2>
              <p className="text-sm text-gray-500">Number of unique visitors</p>
            </div>
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button className="px-3 py-1 bg-white rounded shadow-sm text-xs font-semibold text-gray-900">This Year</button>
              <button className="px-3 py-1 text-xs font-semibold text-gray-500 hover:text-gray-900">Last Year</button>
            </div>
          </div>

          <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={visitData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVisits" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  dy={10}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }}
                />
                <Area
                  type="monotone"
                  dataKey="visits"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorVisits)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Metric Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Metric 1: Conversions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 relative overflow-hidden">
            <div className="flex justify-between items-start mb-2">
              <span className="font-semibold text-gray-900">Conversions</span>
              <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-3xl font-bold text-gray-900">4,123</span>
              <span className="text-xs font-semibold text-red-500 flex items-center">
                <ArrowDown size={12} className="mr-0.5" /> 2% below target
              </span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparklineData1}>
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Metric 2: Impressions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 relative overflow-hidden">
            <div className="flex justify-between items-start mb-2">
              <span className="font-semibold text-gray-900">Impressions</span>
              <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-3xl font-bold text-gray-900">46,085</span>
              <span className="text-xs font-semibold text-red-500 flex items-center">
                <ArrowDown size={12} className="mr-0.5" /> 4% below target
              </span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparklineData2}>
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Metric 3: Visits */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 relative overflow-hidden">
            <div className="flex justify-between items-start mb-2">
              <span className="font-semibold text-gray-900">Visits</span>
              <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-3xl font-bold text-gray-900">62,083</span>
              <span className="text-xs font-semibold text-red-500 flex items-center">
                <ArrowDown size={12} className="mr-0.5" /> 4% below target
              </span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparklineData3}>
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Your Audience Section */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-1">Your Audience</h2>
          <p className="text-sm text-gray-500 mb-6">Demographic properties of your users</p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* New vs Returning */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex justify-between items-center mb-4">
                <span className="font-semibold text-gray-900 text-sm">New vs. Returning</span>
                <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
              </div>
              <div className="h-40 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[{ value: 80 }, { value: 20 }]}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={0}
                      dataKey="value"
                      startAngle={90}
                      endAngle={-270}
                      stroke="none"
                    >
                      <Cell fill={COLORS[0]} />
                      <Cell fill={COLORS[1]} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                {/* Legend */}
                <div className="space-y-3 mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span> New
                    </div>
                    <div className="font-bold text-gray-900">36,868 <span className="text-gray-400 font-normal">80%</span></div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-slate-200"></span> Returning
                    </div>
                    <div className="font-bold text-gray-900">9,217 <span className="text-gray-400 font-normal">20%</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Gender */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex justify-between items-center mb-4">
                <span className="font-semibold text-gray-900 text-sm">Gender</span>
                <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
              </div>
              <div className="h-40 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[{ value: 55 }, { value: 45 }]}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={2}
                      dataKey="value"
                      startAngle={90}
                      endAngle={-270}
                      stroke="none"
                    >
                      <Cell fill={GENDER_COLORS[0]} />
                      <Cell fill={GENDER_COLORS[1]} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                {/* Legend */}
                <div className="space-y-3 mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-teal-400"></span> Male
                    </div>
                    <div className="font-bold text-gray-900">25,346 <span className="text-gray-400 font-normal">55%</span></div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-slate-200"></span> Female
                    </div>
                    <div className="font-bold text-gray-900">20,738 <span className="text-gray-400 font-normal">45%</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Age */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex justify-between items-center mb-4">
                <span className="font-semibold text-gray-900 text-sm">Age</span>
                <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
              </div>
              <div className="h-40 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[{ value: 35 }, { value: 65 }]}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={2}
                      dataKey="value"
                      startAngle={90}
                      endAngle={-270}
                      stroke="none"
                    >
                      <Cell fill={AGE_COLORS[0]} />
                      <Cell fill={AGE_COLORS[1]} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                {/* Legend */}
                <div className="space-y-3 mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-orange-500"></span> Under 30
                    </div>
                    <div className="font-bold text-gray-900">16,129 <span className="text-gray-400 font-normal">35%</span></div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-slate-200"></span> Over 30
                    </div>
                    <div className="font-bold text-gray-900">29,955 <span className="text-gray-400 font-normal">65%</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Language */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex justify-between items-center mb-4">
                <span className="font-semibold text-gray-900 text-sm">Language</span>
                <span className="bg-gray-100 text-gray-500 text-[10px] font-bold px-2 py-0.5 rounded-full">30 days</span>
              </div>
              <div className="h-40 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[{ value: 25 }, { value: 75 }]}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={2}
                      dataKey="value"
                      startAngle={90}
                      endAngle={-270}
                      stroke="none"
                    >
                      <Cell fill={LANG_COLORS[0]} />
                      <Cell fill={LANG_COLORS[1]} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                {/* Legend */}
                <div className="space-y-3 mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-purple-500"></span> English
                    </div>
                    <div className="font-bold text-gray-900">11,521 <span className="text-gray-400 font-normal">25%</span></div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-slate-200"></span> Other
                    </div>
                    <div className="font-bold text-gray-900">34,563 <span className="text-gray-400 font-normal">75%</span></div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsView;