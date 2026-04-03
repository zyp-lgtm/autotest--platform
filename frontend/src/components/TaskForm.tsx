import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useProject } from '../contexts/ProjectContext'
import { tasksApi } from '../api/tasks'

interface TaskFormProps {
  mode?: 'create' | 'edit'
}

export default function TaskForm({ mode = 'create' }: TaskFormProps) {
  const navigate = useNavigate()
  const { taskId } = useParams<{ taskId?: string }>()
  const { currentProject } = useProject()

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: [] as string[]
  })
  const [tagInput, setTagInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (mode === 'edit' && taskId) {
      loadTask(taskId)
    }
  }, [mode, taskId])

  const loadTask = async (id: string) => {
    try {
      setLoading(true)
      const task = await tasksApi.getTask(id)
      setFormData({
        name: task.name,
        description: task.description || '',
        tags: task.tags || []
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!currentProject) {
      setError('请先选择一个项目')
      return
    }

    if (!formData.name.trim()) {
      setError('任务名称不能为空')
      return
    }

    try {
      setLoading(true)
      setError(null)

      if (mode === 'edit' && taskId) {
        await tasksApi.updateTask(taskId, formData)
      } else {
        await tasksApi.createTask(currentProject.id, formData)
      }

      navigate('/tasks')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddTag = () => {
    const tag = tagInput.trim()
    if (tag && !formData.tags.includes(tag)) {
      setFormData({ ...formData, tags: [...formData.tags, tag] })
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddTag()
    }
  }

  if (loading && mode === 'edit') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {mode === 'edit' ? '编辑任务' : '创建任务'}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {currentProject ? `项目: ${currentProject.name}` : '请先选择项目'}
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        {/* 任务名称 */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            任务名称 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="输入任务名称"
            disabled={loading}
          />
        </div>

        {/* 任务描述 */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            任务描述
          </label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={4}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="输入任务描述（可选）"
            disabled={loading}
          />
        </div>

        {/* 标签 */}
        <div>
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
            标签
          </label>
          <div className="mt-1 flex gap-2">
            <input
              type="text"
              id="tags"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="输入标签后按回车添加"
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleAddTag}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
              disabled={loading}
            >
              添加
            </button>
          </div>

          {/* 已添加的标签 */}
          {formData.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {formData.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-blue-900"
                    disabled={loading}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            type="button"
            onClick={() => navigate('/tasks')}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            disabled={loading}
          >
            取消
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            disabled={loading}
          >
            {loading ? '保存中...' : mode === 'edit' ? '保存更改' : '创建任务'}
          </button>
        </div>
      </form>
    </div>
  )
}
