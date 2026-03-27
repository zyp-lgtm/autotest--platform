export interface Project {
  id: number;
  name: string;
  icon: string;
  description: string;
  createdAt: string;
}

export interface CreateProjectInput {
  name: string;
  icon: string;
  description: string;
}

export interface UpdateProjectInput {
  name?: string;
  icon?: string;
  description?: string;
}