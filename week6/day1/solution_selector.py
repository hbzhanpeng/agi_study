from enum import Enum
from dataclasses import dataclass

class Solution(Enum):
    PROMPT = "Prompt Engineering"
    RAG = "RAG"
    FINETUNE = "Fine-tuning"
    RAG_FINETUNE = "RAG + Fine-tuning"

@dataclass
class TaskRequirements:
    needs_external_knowledge: bool
    knowledge_updates_frequently: bool
    has_labeled_data: bool
    needs_specific_style: bool
    budget_high: bool

def select_solution(req: TaskRequirements) -> Solution:
    if req.needs_external_knowledge:
        if req.knowledge_updates_frequently:
            if req.budget_high and req.needs_specific_style:
                return Solution.RAG_FINETUNE
            else:
                return Solution.RAG
        else:
            if req.budget_high and req.needs_specific_style:
                return Solution.FINETUNE
            else:
                return Solution.PROMPT
    else:
        if req.has_labeled_data:
            if req.needs_specific_style:
                return Solution.FINETUNE
            else:
                return Solution.PROMPT
        else:
            return Solution.PROMPT

if __name__ == "__main__":
    test1 = TaskRequirements(
        needs_external_knowledge=True,
        knowledge_updates_frequently=True,
        has_labeled_data=False,
        needs_specific_style=False,
        budget_high=False
    )
    print(f"客服问答: {select_solution(test1).value}")
    
    test2 = TaskRequirements(
        needs_external_knowledge=False,
        knowledge_updates_frequently=False,
        has_labeled_data=False,
        needs_specific_style=False,
        budget_high=False
    )
    print(f"代码生成: {select_solution(test2).value}")
    
    test3 = TaskRequirements(
        needs_external_knowledge=True,
        knowledge_updates_frequently=True,
        has_labeled_data=True,
        needs_specific_style=True,
        budget_high=True
    )
    print(f"法律文书: {select_solution(test3).value}")
    
    test4 = TaskRequirements(
        needs_external_knowledge=True,
        knowledge_updates_frequently=False,
        has_labeled_data=True,
        needs_specific_style=True,
        budget_high=True
    )
    print(f"医疗诊断: {select_solution(test4).value}")
