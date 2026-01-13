
export enum WorkflowStep {
  DASHBOARD = 'DASHBOARD',
  UPLOAD = 'UPLOAD',
  MAP = 'MAP',
  REVIEW = 'REVIEW',
  COMPLETE = 'COMPLETE'
}

export interface Transaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  ticker?: string;
  account: string;
  status: 'ready' | 'error';
  errorMsg?: string;
}
