import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { miniAppApi } from "../api/miniapp";
import type { MiniAppAssistBody, RelationshipCreateBody, RelationshipUpdateBody, RuleBody, WorkflowName } from "../api/types";

export const bootstrapQueryKey = ["bootstrap"] as const;

export function useBootstrapQuery() {
  return useQuery({
    queryKey: bootstrapQueryKey,
    queryFn: miniAppApi.bootstrap,
  });
}

function useBootstrapInvalidatingMutation<TVariables, TResult>(
  mutationFn: (variables: TVariables) => Promise<TResult>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: bootstrapQueryKey });
    },
  });
}

export function useCreateRelationshipMutation() {
  return useBootstrapInvalidatingMutation((body: RelationshipCreateBody) => miniAppApi.createRelationship(body));
}

export function useUpdateRelationshipMutation() {
  return useBootstrapInvalidatingMutation(({ relationshipId, body }: { relationshipId: string; body: RelationshipUpdateBody }) =>
    miniAppApi.updateRelationship(relationshipId, body),
  );
}

export function useDeleteRelationshipMutation() {
  return useBootstrapInvalidatingMutation((relationshipId: string) => miniAppApi.deleteRelationship(relationshipId));
}

export function useSetDefaultRelationshipMutation() {
  return useBootstrapInvalidatingMutation((relationshipId: string) => miniAppApi.setDefaultRelationship(relationshipId));
}

export function useAddRuleMutation() {
  return useBootstrapInvalidatingMutation(({ relationshipId, body }: { relationshipId: string; body: RuleBody }) =>
    miniAppApi.addRule(relationshipId, body),
  );
}

export function useUpdateRuleMutation() {
  return useBootstrapInvalidatingMutation(({ relationshipId, ruleId, body }: { relationshipId: string; ruleId: number; body: RuleBody }) =>
    miniAppApi.updateRule(relationshipId, ruleId, body),
  );
}

export function useDeleteRuleMutation() {
  return useBootstrapInvalidatingMutation(({ relationshipId, ruleId }: { relationshipId: string; ruleId: number }) =>
    miniAppApi.deleteRule(relationshipId, ruleId),
  );
}

export function useAssistMutation() {
  return useMutation({
    mutationFn: ({ workflow, body }: { workflow: WorkflowName; body: MiniAppAssistBody }) =>
      miniAppApi.assist(workflow, body),
  });
}
