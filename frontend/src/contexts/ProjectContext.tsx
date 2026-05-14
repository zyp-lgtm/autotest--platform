import { createContext, useContext, useState, ReactNode, useEffect } from 'react'
import { projectsApi } from '../api/projects'
import { useAuth } from './AuthContext'

interface Project {
  id: string
  name: string
  description?: string
}

interface ProjectContextType {
  currentProject: Project | null
  setCurrentProject: (project: Project) => void
  projects: Project[]
  loading: boolean
  loadProjects: () => Promise<void>
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined)

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const { isAuthenticated } = useAuth()

  // 只在用户已认证后才加载项目列表（避免 401 触发登出重定向）
  useEffect(() => {
    if (isAuthenticated) {
      loadProjects()
    } else {
      setLoading(false)
    }
  }, [isAuthenticated])

  // 当项目列表加载完成后，默认选择第一个项目
  useEffect(() => {
    if (projects.length > 0 && !currentProject) {
      // 优先使用之前选择的项目（从 localStorage）
      const savedProjectId = localStorage.getItem('selectedProjectId')
      if (savedProjectId) {
        const savedProject = projects.find(p => p.id === savedProjectId)
        if (savedProject) {
          setCurrentProject(savedProject)
          return
        }
      }
      // 否则选择第一个有任务的项目
      const projectWithTasks = projects[0] // 可以后续优化，优先选择有任务的项目
      setCurrentProject(projectWithTasks)
    }
  }, [projects])

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects()
      setProjects(data)
    } catch (error) {
      console.error('加载项目列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 包装 setCurrentProject，保存选择到 localStorage
  const handleSetCurrentProject = (project: Project) => {
    setCurrentProject(project)
    localStorage.setItem('selectedProjectId', project.id)
  }

  return (
    <ProjectContext.Provider value={{ currentProject, setCurrentProject: handleSetCurrentProject, projects, loading, loadProjects }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider')
  }
  return context
}
