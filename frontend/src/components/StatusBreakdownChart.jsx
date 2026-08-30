import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function StatusBreakdownChart({ data }) {
  return (
    <div className="h-64 w-full" role="img" aria-label="Application counts by status">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <XAxis type="number" allowDecimals={false} stroke="var(--al-muted)" fontSize={12} />
          <YAxis
            type="category"
            dataKey="status"
            width={96}
            stroke="var(--al-muted)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            cursor={{ fill: 'color-mix(in srgb, var(--al-accent) 12%, transparent)' }}
            contentStyle={{
              background: 'var(--al-surface)',
              border: '1px solid var(--al-line)',
              borderRadius: 8,
              color: 'var(--al-ink)',
            }}
          />
          <Bar dataKey="count" fill="var(--al-accent)" radius={[0, 4, 4, 0]} maxBarSize={22} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default StatusBreakdownChart
