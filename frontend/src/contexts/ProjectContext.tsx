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
    id: '468f7eccc919406082661497eb6a7b2d',
    name: '测试项目',
    description: '默认测试项目',
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
