import React, { useState } from 'react';
import { X, ChevronRight, ChevronLeft } from 'lucide-react';

/**
 * Risk Questionnaire Modal - Interactive multi-step questionnaire
 * Assesses time horizon, risk tolerance, experience, and financial stability
 */
export const RiskQuestionnaireModal = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});

  // Questionnaire structure with 4 questions
  const questions = [
    {
      id: 'time_horizon',
      title: 'Investment Time Horizon',
      subtitle: 'When do you expect to need this money?',
      options: [
        { text: 'Less than 3 years', score: 20, description: 'Short-term goals' },
        { text: '3-5 years', score: 40, description: 'Medium-term goals' },
        { text: '5-10 years', score: 60, description: 'Long-term goals' },
        { text: '10-20 years', score: 80, description: 'Retirement planning' },
        { text: 'More than 20 years', score: 100, description: 'Long-term wealth building' }
      ]
    },
    {
      id: 'risk_tolerance',
      title: 'Risk Tolerance',
      subtitle: 'How would you react to a 20% portfolio decline?',
      options: [
        { text: 'Sell everything immediately', score: 10, description: 'Very risk-averse' },
        { text: 'Sell some holdings', score: 30, description: 'Risk-averse' },
        { text: 'Hold steady and wait', score: 50, description: 'Moderate risk tolerance' },
        { text: 'Buy more while prices are low', score: 70, description: 'Risk-tolerant' },
        { text: 'Aggressively buy the dip', score: 90, description: 'Very risk-tolerant' }
      ]
    },
    {
      id: 'investment_experience',
      title: 'Investment Experience',
      subtitle: 'How would you describe your investment knowledge?',
      options: [
        { text: 'Beginner - New to investing', score: 20, description: 'Just starting out' },
        { text: 'Basic - Understand stocks and bonds', score: 40, description: 'Some knowledge' },
        { text: 'Intermediate - Active investor', score: 60, description: 'Regular trading' },
        { text: 'Advanced - Portfolio management', score: 80, description: 'Experienced' },
        { text: 'Expert - Professional level', score: 100, description: 'Deep expertise' }
      ]
    },
    {
      id: 'financial_stability',
      title: 'Financial Stability',
      subtitle: 'What is your current financial situation?',
      options: [
        { text: 'No emergency fund', score: 10, description: 'Need liquidity' },
        { text: '1-3 months expenses saved', score: 30, description: 'Building reserves' },
        { text: '3-6 months expenses saved', score: 50, description: 'Adequate reserves' },
        { text: '6-12 months expenses saved', score: 70, description: 'Strong reserves' },
        { text: 'Over 12 months saved + stable income', score: 90, description: 'Very stable' }
      ]
    }
  ];

  if (!isOpen) return null;

  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;
  const isFirstStep = currentStep === 0;
  const hasAnswer = answers[currentQuestion.id] !== undefined;

  const handleSelectOption = (optionScore) => {
    setAnswers({
      ...answers,
      [currentQuestion.id]: optionScore
    });
  };

  const handleNext = () => {
    if (isLastStep) {
      handleSubmit();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (!isFirstStep) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = () => {
    // Convert answers to backend format
    const formattedAnswers = Object.entries(answers).map(([question_id, score]) => ({
      question_id,
      score
    }));

    onComplete(formattedAnswers);

    // Reset state
    setCurrentStep(0);
    setAnswers({});
  };

  const progressPercentage = ((currentStep + 1) / questions.length) * 100;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl rounded-[20px] glass-card-strong overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-white border-opacity-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white tracking-wide uppercase">
              Risk Profile Assessment
            </h2>
            <button
              onClick={onClose}
              className="w-10 h-10 rounded-xl bg-white bg-opacity-5 hover:bg-opacity-10 flex items-center justify-center transition-all"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="relative h-2 bg-white bg-opacity-10 rounded-full overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-2 text-xs text-white text-opacity-60">
            <span>Step {currentStep + 1} of {questions.length}</span>
            <span>{Math.round(progressPercentage)}% Complete</span>
          </div>
        </div>

        {/* Question Content */}
        <div className="p-6 min-h-[400px] flex flex-col">
          <div className="mb-6">
            <h3 className="text-xl font-bold text-white mb-2">
              {currentQuestion.title}
            </h3>
            <p className="text-sm text-white text-opacity-70">
              {currentQuestion.subtitle}
            </p>
          </div>

          {/* Options */}
          <div className="space-y-3 flex-1">
            {currentQuestion.options.map((option) => {
              const isSelected = answers[currentQuestion.id] === option.score;

              return (
                <button
                  key={option.score}
                  onClick={() => handleSelectOption(option.score)}
                  className={`w-full p-4 rounded-xl text-left transition-all duration-200 ${
                    isSelected
                      ? 'bg-blue-500 bg-opacity-20 border-2 border-blue-500 border-opacity-50'
                      : 'bg-white bg-opacity-5 border-2 border-transparent hover:bg-opacity-10'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-white mb-1">
                        {option.text}
                      </div>
                      <div className="text-xs text-white text-opacity-60">
                        {option.description}
                      </div>
                    </div>
                    {isSelected && (
                      <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 ml-3">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between mt-6 pt-6 border-t border-white border-opacity-10">
            <button
              onClick={handleBack}
              disabled={isFirstStep}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                isFirstStep
                  ? 'bg-white bg-opacity-5 text-white text-opacity-30 cursor-not-allowed'
                  : 'bg-white bg-opacity-10 text-white hover:bg-opacity-20'
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!hasAnswer}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold transition-all ${
                !hasAnswer
                  ? 'bg-white bg-opacity-5 text-white text-opacity-30 cursor-not-allowed'
                  : 'gradient-blue-button text-white hover:shadow-lg'
              }`}
            >
              {isLastStep ? 'Complete Assessment' : 'Next Question'}
              {!isLastStep && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
