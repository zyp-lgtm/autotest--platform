import React, { useState, useEffect, useCallback } from 'react'
import { keywordsApi, type Keyword } from '../api/keywords'
import { useToast } from '../contexts/ToastContext'

const CATEGORIES = [
  { value: 'ui', label: 'UI' },
  { value: 'api', label: 'API' },
  { value: 'assertion', label: '断言' },
  { value: 'extract', label: '提取' },
  { value: 'data', label: '数据' },
]

const TYPES = [
  { value: 'system', label: '系统' },
  { value: 'action', label: '动作' },
  { value: 'assertion', label: '断言' },
  { value: 'extraction', label: '提取' },
  { value: 'business', label: '业务' },
]

interface KeywordFormData {
  name: string
  keyword_type: string
  category: string
  description: string
  icon: string
  parameter_schema: string
  return_schema: string
  code_content: string
}

const emptyForm = (): KeywordFormData => ({
  name: '',
  keyword_type: 'system',
  category: 'ui',
  description: '',
  icon: '',
  parameter_schema: '{}',
  return_schema: '{}',
  code_content: '',
})

const KeywordsPage: React.FC = () => {
  const toast = useToast()
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [loading, setLoading] = useState(true)
  const [filterCategory, setFilterCategory] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingKeyword, setEditingKeyword] = useState<Keyword | null>(null)
  const [form, setForm] = useState<KeywordFormData>(emptyForm())
  const [saving, setSaving] = useState(false)

  const loadKeywords = useCallback(async () => {
    try {
      setLoading(true)
      const data = await keywordsApi.getKeywords(filterCategory || undefined)
      setKeywords(data)
    } catch (err) {
      toast.error('加载关键字列表失败')
    } finally {
      setLoading(false)
    }
  }, [filterCategory, toast])

  useEffect(() => {
    loadKeywords()
  }, [loadKeywords])

  const openCreate = () => {
    setEditingKeyword(null)
    setForm(emptyForm())
    setShowForm(true)
  }

  const openEdit = (kw: Keyword) => {
    setEditingKeyword(kw)
    setForm({
      name: kw.name,
      keyword_type: kw.parameter_schema?._type || 'system',
      category: kw.category,
      description: kw.description || '',
      icon: '',
      parameter_schema: JSON.stringify(kw.parameter_schema || {}, null, 2),
      return_schema: '{}',
      code_content: '',
    })
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.warning('请输入关键字名称')
      return
    }
    if (!form.category) {
      toast.warning('请选择分类')
      return
    }

    let parameter_schema: Record<string, any> = {}
    try {
      parameter_schema = JSON.parse(form.parameter_schema)
    } catch {
      toast.warning('参数 Schema 格式错误，请输入有效的 JSON')
      return
    }

    let return_schema: Record<string, any> = {}
    try {
      return_schema = JSON.parse(form.return_schema)
    } catch {
      toast.warning('返回 Schema 格式错误，请输入有效的 JSON')
      return
    }

    try {
      setSaving(true)
      const payload = {
        name: form.name.trim(),
        keyword_type: form.keyword_type,
        category: form.category,
        description: form.description,
        icon: form.icon || undefined,
        parameter_schema,
        return_schema,
        code_content: form.code_content || undefined,
      }

      if (editingKeyword) {
        await keywordsApi.updateKeyword(editingKeyword.id, payload)
        toast.success(`关键字 "${form.name}" 已更新`)
      } else {
        await keywordsApi.createKeyword(payload)
        toast.success(`关键字 "${form.name}" 已创建`)
      }
      setShowForm(false)
      loadKeywords()
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || '保存失败'
      toast.error(detail)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (kw: Keyword) => {
    if (!confirm(`确定要删除关键字 "${kw.name}" 吗？`)) return
    try {
      await keywordsApi.deleteKeyword(kw.id)
      toast.success(`关键字 "${kw.name}" 已删除`)
      loadKeywords()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || '删除失败')
    }
  }

  const getCategoryLabel = (cat: string) =>
    CATEGORIES.find(c => c.value === cat)?.label || cat

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">关键字管理</h1>
        <button
          onClick={openCreate}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          创建关键字
        </button>
      </div>

      {/* 分类过滤 */}
      <div className="mb-6 flex items-center gap-2">
        <span className="text-sm text-gray-600">分类过滤:</span>
        <button
          onClick={() => setFilterCategory('')}
          className={`px-3 py-1 text-sm rounded ${
            !filterCategory ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          全部
        </button>
        {CATEGORIES.map(cat => (
          <button
            key={cat.value}
            onClick={() => setFilterCategory(cat.value)}
            className={`px-3 py-1 text-sm rounded ${
              filterCategory === cat.value ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      ) : keywords.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">暂无关键字</p>
          <button
            onClick={openCreate}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            创建第一个关键字
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">分类</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">描述</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {keywords.map(kw => (
                <tr key={kw.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm font-medium text-gray-900">{kw.name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">
                      {getCategoryLabel(kw.category)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                    {kw.description || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        kw.enabled ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEdit(kw)}
                      className="text-blue-500 hover:text-blue-700 text-sm mr-3"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(kw)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 创建/编辑模态框 */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {editingKeyword ? '编辑关键字' : '创建关键字'}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: CLICK"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    分类 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={form.category}
                    onChange={e => setForm({ ...form, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {CATEGORIES.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                  <select
                    value={form.keyword_type}
                    onChange={e => setForm({ ...form, keyword_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="输入关键字描述"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  参数 Schema (JSON)
                </label>
                <textarea
                  value={form.parameter_schema}
                  onChange={e => setForm({ ...form, parameter_schema: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  rows={4}
                  placeholder='{"url": {"type": "string", "required": true}}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  返回 Schema (JSON)
                </label>
                <textarea
                  value={form.return_schema}
                  onChange={e => setForm({ ...form, return_schema: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  rows={3}
                  placeholder='{"status_code": {"type": "number"}}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  代码内容 (业务关键字)
                </label>
                <textarea
                  value={form.code_content}
                  onChange={e => setForm({ ...form, code_content: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  rows={4}
                  placeholder="# 自定义关键字代码"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4 border-t">
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KeywordsPage
