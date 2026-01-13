
import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import UploadStep from './pages/UploadStep';
import MapStep from './pages/MapStep';
import ReviewStep from './pages/ReviewStep';
import CompleteStep from './pages/CompleteStep';
import { WorkflowStep } from './types';

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>(WorkflowStep.DASHBOARD);

  const renderContent = () => {
    switch (currentStep) {
      case WorkflowStep.DASHBOARD:
        return <Dashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
      case WorkflowStep.UPLOAD:
        return <UploadStep onNext={() => setCurrentStep(WorkflowStep.MAP)} onBack={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
      case WorkflowStep.MAP:
        return <MapStep onNext={() => setCurrentStep(WorkflowStep.REVIEW)} onBack={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
      case WorkflowStep.REVIEW:
        return <ReviewStep onNext={() => setCurrentStep(WorkflowStep.COMPLETE)} onBack={() => setCurrentStep(WorkflowStep.MAP)} />;
      case WorkflowStep.COMPLETE:
        return <CompleteStep onFinish={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
      default:
        return <Dashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
    }
  };

  return (
    <Layout currentStep={currentStep}>
      {renderContent()}
    </Layout>
  );
};

export default App;
