import type { Project } from '../types/project';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface ProjectSelectorProps {
  projects: Project[];
  selectedId: number;
  onChange: (id: number) => void;
  className?: string;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  projects, selectedId, onChange, className = ''
}) => {
  return (
    <Select value={String(selectedId)} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger className={`h-9 px-3 py-2 border-2 border-gray-200 rounded-lg text-sm flex-1 min-w-[140px] ${className}`}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {projects.map(project => (
          <SelectItem key={project.id} value={String(project.id)}>
            {project.icon} {project.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};