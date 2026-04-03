import { useState, useEffect } from 'react'
import { keywordsApi, Keyword } from '../api/keywords'

interface KeywordSelectorProps {
  value?: string
  onChange: (keywordId: string) => void
  category?: string
  disabled?: boolean
}

export default function KeywordSelector({ value, onChange, category, disabled }: KeywordSelectorProps) {
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>(category || 'all')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [showExamples, setShowExamples] = useState<string | null>(null)

  useEffect(() => {
    loadCategories()
    loadKeywords()
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      const cats = await keywordsApi.getCategories()
      setCategories(['all', ...cats])
    } catch (err) {
      console.error('加载类别失败:', err)
    }
  }

  const loadKeywords = async () => {
    try {
      setLoading(true)
      const cat = selectedCategory === 'all' ? undefined : selectedCategory
      const data = await keywordsApi.getKeywords(cat)
      setKeywords(data)
    } catch (err) {
      console.error('加载关键字失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredKeywords = keywords.filter(kw =>
    kw.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    kw.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const selectedKeyword = keywords.find(kw => kw.id === value)

  // 按类别分组显示
  const groupedKeywords = selectedCategory === 'all'
    ? filteredKeywords.reduce((acc, kw) => {
        if (!acc[kw.category]) acc[kw.category] = []
        acc[kw.category].push(kw)
        return acc
      }, {} as Record<string, Keyword[]>)
    : { [selectedCategory]: filteredKeywords }

  return (
    <div className="space-y-4">
      {/* 选择器头部 */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {selectedKeyword ? (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-blue-900">{selectedKeyword.name}</div>
                  <div className="text-sm text-blue-700">{selectedKeyword.description}</div>
                  <div className="text-xs text-blue-600 mt-1">类别: {selectedKeyword.category}</div>
                </div>
                {!disabled && (
                  <button
                    onClick={() => onChange('')}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    更换
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">请选择关键字</div>
          )}
        </div>
      </div>

      {/* 关键字选择面板 */}
      {(!selectedKeyword || disabled === false) && (
        <div className="border border-gray-200 rounded-lg p-4 space-y-4">
          {/* 搜索和过滤 */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="搜索关键字..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? '全部类别' : cat}
                </option>
              ))}
            </select>
          </div>

          {/* 关键字列表 */}
          {loading ? (
            <div className="text-center text-gray-500 py-4">加载中...</div>
          ) : (
            <div className="max-h-64 overflow-y-auto space-y-3">
              {Object.entries(groupedKeywords).map(([cat, kws]) => (
                <div key={cat}>
                  <div className="text-sm font-medium text-gray-700 mb-2">{cat}</div>
                  <div className="space-y-1 ml-2">
                    {kws.map((kw) => (
                      <div key={kw.id}>
                        <div className="flex items-start justify-between group">
                          <button
                            onClick={() => onChange(kw.id)}
                            disabled={disabled}
                            className={`flex-1 text-left p-2 rounded hover:bg-gray-50 transition ${
                              disabled ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                          >
                            <div className="font-medium text-sm">{kw.name}</div>
                            <div className="text-xs text-gray-500">{kw.description}</div>
                          </button>
                          {kw.examples && kw.examples.length > 0 && (
                            <button
                              onClick={() => setShowExamples(showExamples === kw.id ? null : kw.id)}
                              className="text-xs text-blue-600 hover:text-blue-800 ml-2"
                            >
                              示例
                            </button>
                          )}
                        </div>
                        {showExamples === kw.id && kw.examples && (
                          <div className="ml-4 mt-1 p-2 bg-gray-50 rounded text-xs">
                            <div className="font-medium mb-1">参数示例:</div>
                            <pre className="text-gray-600 whitespace-pre-wrap">
                              {JSON.stringify(kw.examples[0], null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {filteredKeywords.length === 0 && (
                <div className="text-center text-gray-500 py-4">没有找到匹配的关键字</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
