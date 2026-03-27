import { useState, useEffect } from 'react';
import type { Project, CreateProjectInput, UpdateProjectInput } from '../types/project';
import { projectStorage, DEFAULT_PROJECT } from '../utils/storage-projects';

export const useProjects = () => {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    const loaded = projectStorage.getProjects();
    setProjects(loaded);
  }, []);

  useEffect(() => {
    if (projects.length > 0) {
      projectStorage.saveProjects(projects);
    }
  }, [projects]);

  const addProject = (input: CreateProjectInput) => {
    const newProject: Project = {
      id: Date.now(),
      ...input,
      createdAt: new Date().toISOString()
    };
    setProjects(prev => [...prev, newProject]);
  };

  const updateProject = (id: number, input: UpdateProjectInput) => {
    setProjects(prev =>
      prev.map(project =>
        project.id === id ? { ...project, ...input } : project
      )
    );
  };

  const deleteProject = (id: number) => {
    if (projectStorage.isDefaultProject(id)) {
      return false;
    }
    setProjects(prev => prev.filter(project => project.id !== id));
    return true;
  };

  const getProject = (id: number): Project | undefined => {
    return projects.find(p => p.id === id);
  };

  const getProjectTaskCount = (projectId: number, tasks: { projectId: number }[]): number => {
    return tasks.filter(task => task.projectId === projectId).length;
  };

  const defaultProject = DEFAULT_PROJECT;

  return {
    projects,
    addProject,
    updateProject,
    deleteProject,
    getProject,
    getProjectTaskCount,
    defaultProject
  };
};