import { useState } from 'react'

function Dashboard() {
  const [stats, setStats] = useState({
    totalTasks: 0,
    totalScenarios: 0,
    totalCases: 0,
  })

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">仪表盘</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">总任务数</h3>
          <p className="text-3xl font-bold">{stats.totalTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">总场景数</h3>
          <p className="text-3xl font-bold">{stats.totalScenarios}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">总用例数</h3>
          <p className="text-3xl font-bold">{stats.totalCases}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">快捷操作</h2>
        <div className="grid grid-cols-2 gap-4">
          <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            创建任务
          </button>
          <button className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
            管理数据
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard