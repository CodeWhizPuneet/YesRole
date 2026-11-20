import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function TrendChart({ data }: { data: { date: string; score: number; role: string }[] }) {
  return <div className="trend-chart"><ResponsiveContainer width="100%" height={215}>
    <AreaChart data={data} margin={{ left: -24, bottom: 0, right: 15 }}>
      <CartesianGrid stroke="#263247" vertical={false} strokeDasharray="4 4" />
      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
      <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
      <Tooltip labelFormatter={(_, points) => points[0]?.payload?.role ?? ''} contentStyle={{ background: '#151e30', borderColor: '#263247' }} />
      <Area type="monotone" dataKey="score" name="Match score" stroke="#21d4b4" strokeWidth={2} fill="#21d4b4" fillOpacity={0.12} dot isAnimationActive={false} />
    </AreaChart>
  </ResponsiveContainer></div>
}

