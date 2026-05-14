interface TableEditorProps {
  columns: string[];
  rows: Record<string, any>[];
  onRowsChange: (rows: Record<string, any>[]) => void;
  onColumnsChange: (columns: string[]) => void;
  readOnly?: boolean;
}

export function TableEditor({ columns, rows, onRowsChange, onColumnsChange, readOnly }: TableEditorProps) {
  const addRow = () => {
    const lastRow = rows[rows.length - 1] || {};
    const newRow = { ...lastRow };
    onRowsChange([...rows, newRow]);
  };

  const deleteRow = (index: number) => {
    if (!confirm(`删除第 ${index + 1} 行？`)) return;
    onRowsChange(rows.filter((_, i) => i !== index));
  };

  const updateCell = (rowIndex: number, col: string, value: string) => {
    const updated = rows.map((row, i) =>
      i === rowIndex ? { ...row, [col]: value } : row
    );
    onRowsChange(updated);
  };

  const addColumn = () => {
    const name = prompt('新变量名（英文）:');
    if (!name || columns.includes(name)) return;
    onColumnsChange([...columns, name]);
    onRowsChange(rows.map(row => ({ ...row, [name]: '' })));
  };

  const deleteColumn = (col: string) => {
    if (!confirm(`删除列 "${col}"？同时会删除所有行中该字段的值。`)) return;
    onColumnsChange(columns.filter(c => c !== col));
    onRowsChange(rows.map(({ [col]: _, ...rest }) => rest));
  };

  if (rows.length === 0 && columns.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        暂无测试数据，点击下方按钮添加
        {!readOnly && (
          <div className="mt-2">
            <button onClick={addColumn} className="px-4 py-2 bg-blue-600 text-white rounded">+ 添加列</button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border border-gray-300 p-2 bg-gray-100 w-20 text-center text-sm text-gray-600">#</th>
            {columns.map(col => (
              <th key={col} className="border border-gray-300 p-2 bg-gray-100 group text-sm">
                <span className="font-mono text-blue-700">{col}</span>
                {!readOnly && (
                  <button onClick={() => deleteColumn(col)}
                    className="ml-2 text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 text-xs">×</button>
                )}
              </th>
            ))}
            {!readOnly && (
              <th className="border border-gray-300 p-2 bg-gray-100 w-12">
                <button onClick={addColumn} className="text-blue-600 hover:text-blue-800 text-lg leading-none" title="添加列">+</button>
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="hover:bg-blue-50">
              <td className="border border-gray-300 p-2 text-gray-500 text-center text-sm">第{ri + 1}行</td>
              {columns.map(col => (
                <td key={col} className="border border-gray-300 p-0">
                  {readOnly ? (
                    <span className="block p-2 text-sm">{row[col] ?? ''}</span>
                  ) : (
                    <input
                      value={row[col] ?? ''}
                      onChange={e => updateCell(ri, col, e.target.value)}
                      className="w-full p-2 border-0 outline-none focus:bg-blue-50 transition text-sm"
                      placeholder="(空)"
                    />
                  )}
                </td>
              ))}
              {!readOnly && (
                <td className="border border-gray-300 p-1 text-center">
                  <button onClick={() => deleteRow(ri)}
                    className="text-red-400 hover:text-red-600 text-lg leading-none" title="删除行">×</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {!readOnly && (
        <button onClick={addRow} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">
          + 添加行
        </button>
      )}
    </div>
  );
}
