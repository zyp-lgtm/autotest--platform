import { useState } from 'react'

interface ElementPickerProps {
  onElementSelected: (selector: string) => void
  onClose: () => void
}

export default function ElementPicker({ onElementSelected, onClose }: ElementPickerProps) {
  const [selectedSelector, setSelectedSelector] = useState('')

  const steps = [
    {
      number: 1,
      title: '准备测试页面',
      description: '在另一个浏览器标签页中打开您要测试的网页',
      icon: '🌐'
    },
    {
      number: 2,
      title: '打开浏览器开发者工具',
      description: '按 F12 或右键点击页面选择"检查"元素',
      icon: '🔧'
    },
    {
      number: 3,
      title: '使用元素选择器',
      description: '点击开发者工具左上角的选择器图标（Ctrl+Shift+C）',
      icon: '🎯'
    },
    {
      number: 4,
      title: '选择目标元素',
      description: '将鼠标悬停在页面上，点击您要测试的元素',
      icon: '👆'
    },
    {
      number: 5,
      title: '复制选择器',
      description: '在开发者工具中右键点击高亮的元素，选择"Copy" > "Copy selector"',
      icon: '📋'
    }
  ]

  const selectorExamples = [
    {
      name: 'ID选择器',
      example: '#username-input',
      description: '通过元素的ID属性选择'
    },
    {
      name: '类选择器',
      example: '.login-button',
      description: '通过元素的class属性选择'
    },
    {
      name: '属性选择器',
      example: '[data-testid="submit"]',
      description: '通过自定义属性选择（推荐）'
    },
    {
      name: '组合选择器',
      example: 'form input[type="text"]',
      description: '通过层级关系选择'
    }
  ]

  const handleConfirm = () => {
    if (selectedSelector.trim()) {
      onElementSelected(selectedSelector.trim())
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
        {/* 头部 */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">元素选择器指南</h2>
            <p className="text-sm text-gray-500 mt-1">学习如何准确选择网页元素进行测试</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* 快速开始指南 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">🚀 快速开始（5步完成）</h3>
            <div className="space-y-3">
              {steps.map((step) => (
                <div key={step.number} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                    {step.number}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-900">{step.title}</h4>
                    <p className="text-sm text-blue-700">{step.description}</p>
                  </div>
                  <div className="text-2xl">{step.icon}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 选择器示例 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">📝 常用选择器类型</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {selectorExamples.map((example) => (
                <div key={example.name} className="border rounded-lg p-3 hover:shadow-md transition">
                  <div className="font-medium text-gray-900 mb-1">{example.name}</div>
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded block mb-2">
                    {example.example}
                  </code>
                  <p className="text-xs text-gray-500">{example.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 测试选择器 */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-green-900 mb-3">✨ 测试您的选择器</h3>
            <p className="text-sm text-green-700 mb-3">
              将您复制的CSS选择器粘贴到下方，然后点击"确认选择"
            </p>
            <div className="space-y-3">
              <input
                type="text"
                value={selectedSelector}
                onChange={(e) => setSelectedSelector(e.target.value)}
                placeholder="例如: #username-input 或 .login-button"
                className="w-full px-4 py-2 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleConfirm}
                  disabled={!selectedSelector.trim()}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  确认选择
                </button>
                <button
                  onClick={() => setSelectedSelector('')}
                  className="px-4 py-2 border border-green-600 text-green-600 rounded-lg hover:bg-green-50 transition"
                >
                  清空
                </button>
              </div>
            </div>
          </div>

          {/* 最佳实践 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">💡 最佳实践建议</h3>
            <ul className="space-y-2 text-sm text-yellow-800">
              <li className="flex items-start gap-2">
                <span className="text-yellow-600">✓</span>
                <span>优先使用 <strong>data-testid</strong> 等自定义属性，选择器更稳定</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-600">✓</span>
                <span>避免使用过于复杂的CSS选择器，简单选择器更容易维护</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-600">✓</span>
                <span>ID选择器（#id）是最快最稳定的选择方式</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-600">✓</span>
                <span>避免使用索引选择器（如 :nth-child()），页面结构变化时会失效</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-600">✓</span>
                <span>选择器应该在开发者工具的控制台中测试通过后再使用</span>
              </li>
            </ul>
          </div>

          {/* 快捷键提示 */}
          <div className="text-center text-sm text-gray-500">
            <p>💻 <strong>快捷键提示</strong></p>
            <div className="flex justify-center gap-6 mt-2">
              <span><kbd className="bg-gray-100 px-2 py-1 rounded">F12</kbd> 打开开发者工具</span>
              <span><kbd className="bg-gray-100 px-2 py-1 rounded">Ctrl+Shift+C</kbd> 元素选择器</span>
              <span><kbd className="bg-gray-100 px-2 py-1 rounded">Ctrl+F</kbd> 搜索元素</span>
            </div>
          </div>
        </div>

        {/* 底部按钮 */}
        <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedSelector.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            使用该选择器
          </button>
        </div>
      </div>
    </div>
  )
}