import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { toErrorStatus } from "../../api/errors";
import { useAppLanguage, useT } from "../../app/AppProviders";
import { ErrorState } from "../../components/common";
import { Button, Card, Input, Notice, Stack, TextArea } from "../../components/ui";
import { useAddRuleMutation, useCreateRelationshipMutation } from "../../state/queries";
import { RELATION_TYPE_MAX_LENGTH, parseAliases } from "../relationships/format";
import { RULE_TYPE_MAX_LENGTH, validateRule } from "../relationships/RuleForm";

export function OnboardingScreen() {
  const dict = useT();
  const { language } = useAppLanguage();
  const navigate = useNavigate();
  const createRelationship = useCreateRelationshipMutation();
  const addRule = useAddRuleMutation();
  const [relationType, setRelationType] = useState("");
  const [aliases, setAliases] = useState("");
  const [ruleType, setRuleType] = useState("");
  const [ruleValue, setRuleValue] = useState("");
  const [createdId, setCreatedId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<unknown>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setRequestError(null);

    const wantsRule = ruleType.trim().length > 0 || ruleValue.trim().length > 0;
    const ruleCheck = wantsRule ? validateRule({ type: ruleType, value: ruleValue, priority: "0" }, dict) : null;
    if (ruleCheck && !ruleCheck.rule) {
      setValidationError(ruleCheck.error);
      return;
    }
    setValidationError(null);

    try {
      let relationshipId = createdId;
      if (!relationshipId) {
        const created = await createRelationship.mutateAsync({
          relation_type: relationType.trim() || null,
          aliases: parseAliases(aliases),
          communication_style: {},
          set_as_default: true,
        });
        relationshipId = created.relationship_id;
        setCreatedId(relationshipId);
      }
      if (ruleCheck?.rule) {
        await addRule.mutateAsync({ relationshipId, body: ruleCheck.rule });
      }
      navigate("/", { replace: true });
    } catch (err) {
      setRequestError(err);
    }
  }

  const pending = createRelationship.isPending || addRule.isPending;

  return (
    <form onSubmit={onSubmit} noValidate>
      <Stack>
        <h1>{dict.onboardingTitle}</h1>
        {requestError ? <ErrorState language={language} status={toErrorStatus(requestError)} /> : null}
        <Card>
          <Input
            label={dict.relationType}
            value={relationType}
            maxLength={RELATION_TYPE_MAX_LENGTH}
            disabled={createdId !== null}
            onChange={(event) => setRelationType(event.target.value)}
          />
          <Input
            label={dict.aliases}
            value={aliases}
            disabled={createdId !== null}
            onChange={(event) => setAliases(event.target.value)}
          />
        </Card>
        <Notice>{dict.onboardingRuleHint}</Notice>
        <Card>
          <Input
            label={dict.ruleType}
            value={ruleType}
            maxLength={RULE_TYPE_MAX_LENGTH}
            onChange={(event) => setRuleType(event.target.value)}
          />
          <TextArea label={dict.ruleValue} value={ruleValue} onChange={(event) => setRuleValue(event.target.value)} />
        </Card>
        {validationError ? <Notice tone="error">{validationError}</Notice> : null}
        <Button type="submit" stretched disabled={pending} loading={pending}>
          {dict.create}
        </Button>
      </Stack>
    </form>
  );
}
