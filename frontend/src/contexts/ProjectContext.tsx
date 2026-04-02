import { createContext, useContext, useState, ReactNode, useEffect } from 'react'

interface Project {
  id: string
  name: string
  description?: string
}

interface ProjectContextType {
  currentProject: Project | null
  setCurrentProject: (project: Project) => void
  projects: Project[]
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined)

// TODO: 从 API 获取项目列表
const MOCK_PROJECTS: Project[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: '测试项目1',
    description: '第一个测试项目',
  },
]

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [projects] = useState<Project[]>(MOCK_PROJECTS)

  // 默认选择第一个项目
  useEffect(() => {
    if (projects.length > 0 && !currentProject) {
      setCurrentProject(projects[0])
    }
  }, [])

  return (
    <ProjectContext.Provider value={{ currentProject, setCurrentProject, projects }}>
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
