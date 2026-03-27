import { useTasks } from './hooks/useTasks';
import { TaskInput } from './components/TaskInput';
import { TaskList } from './components/TaskList';
import { TaskFilters } from './components/TaskFilters';
import { TaskSort } from './components/TaskSort';
import { TaskStats } from './components/TaskStats';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { TaskSelectionBar } from './components/TaskSelectionBar';
import { BatchActionBar } from './components/BatchActionBar';
import { useTranslation } from './hooks/useTranslation';
import type { Priority } from './types/task';
import { useState } from 'react';

function App() {
  const { t } = useTranslation();
  const {
    tasks,
    filter,
    setFilter,
    sort,
    setSort,
    addTask,
    toggleTask,
    deleteTask,
    updateTask,
    clearCompleted,
    batchDelete,
    batchComplete,
    stats
  } = useTasks();

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const handleAddTask = (text: string, priority: Priority, dueDate: string | null) => {
    addTask(text, priority, dueDate, 1, []); // Default project 1, empty tags
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(tasks.map(task => task.id)));
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleBatchComplete = () => {
    batchComplete(Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  const handleBatchDelete = () => {
    batchDelete(Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center p-4 sm:p-6">
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl w-full max-w-[580px] p-6 sm:p-8 relative">
        <div className="absolute top-5 right-5">
          <LanguageSwitcher />
        </div>

        <h1 className="text-center text-gray-800 mb-7 text-2xl sm:text-3xl font-bold pr-12">{t.app.title}</h1>

        <TaskInput onAdd={handleAddTask} />

        <div className="flex flex-wrap items-center justify-between gap-3 mb-5 pb-4 border-b border-gray-100">
          <TaskFilters filter={filter} onFilterChange={setFilter} />
          <TaskSort sort={sort} onSortChange={setSort} />
        </div>

        <TaskSelectionBar
          selectedCount={selectedIds.size}
          totalCount={tasks.length}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
        />

        {selectedIds.size > 0 && (
          <BatchActionBar
            selectedCount={selectedIds.size}
            onComplete={handleBatchComplete}
            onDelete={handleBatchDelete}
            onCancel={handleDeselectAll}
          />
        )}

        <TaskList
          tasks={tasks}
          onToggle={toggleTask}
          onDelete={deleteTask}
          onUpdate={updateTask}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
        />

        <TaskStats
          activeCount={stats.activeCount}
          overdueCount={stats.overdueCount}
          onClearCompleted={clearCompleted}
        />
      </div>
    </div>
  );
}

export default App;
