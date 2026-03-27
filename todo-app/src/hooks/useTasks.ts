import { useState, useEffect, useMemo } from 'react';
import type { Task, FilterType, SortType, Priority, ProjectFilterType, TagFilterType } from '../types/task';
import { PRIORITIES } from '../constants/priorities';
import { storage, projectStorage } from '../utils/storage';
import { isOverdue } from '../utils/date';

export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<FilterType>('all');
  const [sort, setSort] = useState<SortType>('created');
  const [projectFilter, setProjectFilter] = useState<ProjectFilterType>('all');
  const [tagFilter, setTagFilter] = useState<TagFilterType>('all');

  // Load tasks from localStorage on mount
  useEffect(() => {
    const savedTasks = storage.getTasks();
    const defaultProjectId = projectStorage.getDefaultProjectId();

    // Data migration: ensure old tasks have projectId and tagIds
    const migratedTasks = savedTasks.map(task => ({
      ...task,
      projectId: task.projectId ?? defaultProjectId,
      tagIds: task.tagIds ?? []
    }));

    setTasks(migratedTasks);
  }, []);

  // Save tasks to localStorage whenever they change
  useEffect(() => {
    if (tasks.length > 0 || storage.getTasks().length > 0) {
      storage.saveTasks(tasks);
    }
  }, [tasks]);

  const addTask = (text: string, priority: Priority, dueDate: string | null, projectId: number, tagIds: number[] = []) => {
    const newTask: Task = {
      id: Date.now(),
      text,
      completed: false,
      priority,
      dueDate,
      projectId,
      tagIds,
      createdAt: new Date().toISOString()
    };
    setTasks(prev => [newTask, ...prev]);
  };

  const toggleTask = (id: number) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  };

  const deleteTask = (id: number) => {
    setTasks(prev => prev.filter(task => task.id !== id));
  };

  const updateTask = (id: number, updates: Partial<Pick<Task, 'text' | 'priority' | 'dueDate' | 'projectId' | 'tagIds'>>) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === id ? { ...task, ...updates } : task
      )
    );
  };

  const clearCompleted = () => {
    setTasks(prev => prev.filter(task => !task.completed));
  };

  const batchDelete = (ids: number[]) => {
    setTasks(prev => prev.filter(task => !ids.includes(task.id)));
  };

  const batchComplete = (ids: number[]) => {
    setTasks(prev =>
      prev.map(task =>
        ids.includes(task.id) ? { ...task, completed: true } : task
      )
    );
  };

  // Filter tasks
  const filteredTasks = useMemo(() => {
    let result: Task[];

    switch (filter) {
      case 'active':
        result = tasks.filter(task => !task.completed);
        break;
      case 'completed':
        result = tasks.filter(task => task.completed);
        break;
      default:
        result = tasks;
    }

    // Apply project filter
    if (projectFilter !== 'all') {
      result = result.filter(task => task.projectId === projectFilter);
    }

    // Apply tag filter
    if (tagFilter !== 'all' && tagFilter.length > 0) {
      result = result.filter(task =>
        task.tagIds.some(tagId => tagFilter.includes(tagId))
      );
    }

    return result;
  }, [tasks, filter, projectFilter, tagFilter]);

  // Sort tasks
  const sortedTasks = useMemo(() => {
    const sorted = [...filteredTasks];
    switch (sort) {
      case 'priority':
        sorted.sort((a, b) => PRIORITIES[b.priority].value - PRIORITIES[a.priority].value);
        break;
      case 'dueDate':
        sorted.sort((a, b) => {
          if (!a.dueDate) return 1;
          if (!b.dueDate) return -1;
          return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
        });
        break;
      case 'created':
      default:
        sorted.sort((a, b) => b.id - a.id);
    }
    return sorted;
  }, [filteredTasks, sort]);

  // Stats
  const stats = useMemo(() => {
    const activeCount = tasks.filter(t => !t.completed).length;
    const overdueCount = tasks.filter(t => !t.completed && isOverdue(t.dueDate)).length;
    return { activeCount, overdueCount };
  }, [tasks]);

  return {
    tasks: sortedTasks,
    filter,
    setFilter,
    sort,
    setSort,
    projectFilter,
    setProjectFilter,
    tagFilter,
    setTagFilter,
    addTask,
    toggleTask,
    deleteTask,
    updateTask,
    clearCompleted,
    batchDelete,
    batchComplete,
    stats
  };
};
