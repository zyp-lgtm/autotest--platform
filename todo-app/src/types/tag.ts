export interface Tag {
  id: number;
  name: string;
  description: string;
  createdAt: string;
}

export interface CreateTagInput {
  name: string;
  description: string;
}

export interface UpdateTagInput {
  name?: string;
  description?: string;
}