import { type FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { toErrorStatus } from "../../api/errors";
import type { RelationshipRule, RelationshipView, RuleBody } from "../../api/types";
import { useAppLanguage, useT } from "../../app/AppProviders";
import { ConfirmDialog, EmptyState, ErrorState, LoadingState } from "../../components/common";
import { Button, Card, Input, ListCell, ListSection, Notice, Row, Stack } from "../../components/ui";
import {
  useAddRuleMutation,
  useBootstrapQuery,
  useDeleteRuleMutation,
  useUpdateRelationshipMutation,
  useUpdateRuleMutation,
} from "../../state/queries";
import { attachBackButton } from "../../telegram";
import { RELATION_TYPE_MAX_LENGTH, parseAliases, relationshipLabel } from "./format";
import { RuleForm } from "./RuleForm";

function RelationshipEditForm({
  relationship,
  onError,
}: {
  relationship: RelationshipView;
  onError: (err: unknown) => void;
}) {
  const dict = useT();
  const updateRelationship = useUpdateRelationshipMutation();
  const [relationType, setRelationType] = useState(relationship.relation_type ?? "");
  const [aliases, setAliases] = useState(relationship.aliases.join(", "));
  const [validationError, setValidationError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmedType = relationType.trim();
    // PATCH treats null/absent as "unchanged", so an existing relation type cannot be cleared.
    if (!trimmedType && relationship.relation_type) {
      setValidationError(dict.validationRelationTypeRequired);
      return;
    }
    setValidationError(null);
    try {
      await updateRelationship.mutateAsync({
        relationshipId: relationship.relationship_id,
        body: {
          ...(trimmedType ? { relation_type: trimmedType } : {}),
          aliases: parseAliases(aliases),
        },
      });
    } catch (err) {
      onError(err);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate>
      <Card header={dict.edit}>
        <Input
          label={dict.relationType}
          value={relationType}
          maxLength={RELATION_TYPE_MAX_LENGTH}
          onChange={(event) => setRelationType(event.target.value)}
        />
        <Input label={dict.aliases} value={aliases} onChange={(event) => setAliases(event.target.value)} />
        <Stack>
          {validationError ? <Notice tone="error">{validationError}</Notice> : null}
          <Button type="submit" disabled={updateRelationship.isPending} loading={updateRelationship.isPending}>
            {dict.save}
          </Button>
        </Stack>
      </Card>
    </form>
  );
}

function sortRules(rules: RelationshipRule[]): RelationshipRule[] {
  return [...rules].sort((left, right) => right.priority - left.priority);
}

export function RelationshipDetailsScreen() {
  const dict = useT();
  const { language } = useAppLanguage();
  const navigate = useNavigate();
  const { relationshipId = "" } = useParams();
  const bootstrap = useBootstrapQuery();
  const addRule = useAddRuleMutation();
  const updateRule = useUpdateRuleMutation();
  const deleteRule = useDeleteRuleMutation();
  const [adding, setAdding] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null);
  const [pendingDeleteRuleId, setPendingDeleteRuleId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);

  useEffect(() => attachBackButton(() => navigate("/relationships")), [navigate]);

  if (bootstrap.isPending) {
    return <LoadingState language={language} />;
  }
  if (bootstrap.isError) {
    return (
      <ErrorState
        language={language}
        status={toErrorStatus(bootstrap.error)}
        onRetry={() => {
          void bootstrap.refetch();
        }}
      />
    );
  }

  const relationship = bootstrap.data.relationships.find((item) => item.relationship_id === relationshipId);
  if (!relationship) {
    return (
      <Stack>
        <Notice tone="error">{dict.relationshipNotFound}</Notice>
        <Button onClick={() => navigate("/relationships")}>{dict.back}</Button>
      </Stack>
    );
  }

  async function submitNewRule(body: RuleBody) {
    setActionError(null);
    try {
      await addRule.mutateAsync({ relationshipId, body });
      setAdding(false);
    } catch (err) {
      setActionError(err);
    }
  }

  async function submitRuleUpdate(ruleId: number, body: RuleBody) {
    setActionError(null);
    try {
      await updateRule.mutateAsync({ relationshipId, ruleId, body });
      setEditingRuleId(null);
    } catch (err) {
      setActionError(err);
    }
  }

  async function confirmRuleDelete() {
    const ruleId = pendingDeleteRuleId;
    setPendingDeleteRuleId(null);
    if (ruleId === null) {
      return;
    }
    setActionError(null);
    try {
      await deleteRule.mutateAsync({ relationshipId, ruleId });
    } catch (err) {
      setActionError(err);
    }
  }

  const rules = sortRules(relationship.rules);

  return (
    <Stack>
      <Row>
        <Button mode="plain" onClick={() => navigate("/relationships")}>
          {dict.back}
        </Button>
      </Row>
      <h1>{relationshipLabel(relationship, dict)}</h1>
      {actionError ? <ErrorState language={language} status={toErrorStatus(actionError)} /> : null}
      <RelationshipEditForm key={relationship.relationship_id} relationship={relationship} onError={setActionError} />
      <ListSection header={dict.rules}>
        {rules.length === 0 ? <EmptyState message={dict.noRules} /> : null}
        {rules.map((rule) => {
          const ruleId = rule.id;
          if (ruleId != null && editingRuleId === ruleId) {
            return (
              <RuleForm
                key={ruleId}
                dict={dict}
                initial={{ type: rule.type, value: rule.value, priority: rule.priority }}
                submitLabel={dict.save}
                pending={updateRule.isPending}
                onSubmit={(body) => {
                  void submitRuleUpdate(ruleId, body);
                }}
                onCancel={() => setEditingRuleId(null)}
              />
            );
          }
          return (
            <div key={ruleId ?? `${rule.type}-${rule.value}`} data-testid={`rule-${ruleId ?? "new"}`}>
              <ListCell subtitle={`${rule.type} · ${dict.rulePriority}: ${rule.priority}`}>{rule.value}</ListCell>
              {ruleId != null ? (
                <Stack>
                  <Row>
                    <Button mode="bezeled" aria-label={`${dict.edit}: ${rule.value}`} onClick={() => setEditingRuleId(ruleId)}>
                      {dict.edit}
                    </Button>
                    <Button
                      mode="plain"
                      aria-label={`${dict.delete}: ${rule.value}`}
                      onClick={() => setPendingDeleteRuleId(ruleId)}
                    >
                      {dict.delete}
                    </Button>
                  </Row>
                </Stack>
              ) : null}
            </div>
          );
        })}
      </ListSection>
      {adding ? (
        <Card header={dict.addRule}>
          <RuleForm
            dict={dict}
            submitLabel={dict.addRule}
            pending={addRule.isPending}
            onSubmit={(body) => {
              void submitNewRule(body);
            }}
            onCancel={() => setAdding(false)}
          />
        </Card>
      ) : (
        <Button onClick={() => setAdding(true)}>{dict.addRule}</Button>
      )}
      {pendingDeleteRuleId !== null ? (
        <ConfirmDialog
          language={language}
          message={dict.deleteRuleConfirm}
          onConfirm={() => {
            void confirmRuleDelete();
          }}
          onCancel={() => setPendingDeleteRuleId(null)}
        />
      ) : null}
    </Stack>
  );
}
