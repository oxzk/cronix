import { RefreshCcw } from "lucide-react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { Children, isValidElement, useState, type ReactNode, type SyntheticEvent } from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export interface EmptyStateProps {
  title: string;
  description?: string;
}

/**
 * 空状态展示。
 */
export function EmptyState({ title, description }: EmptyStateProps): JSX.Element {
  return (
    <Card>
      <CardContent className="flex min-h-36 flex-col items-center justify-center gap-2 p-8 text-center">
        <div className="text-sm font-medium">{title}</div>
        {description ? <div className="max-w-md text-sm text-muted-foreground">{description}</div> : null}
      </CardContent>
    </Card>
  );
}

export interface SectionHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  onRefresh?: () => void;
  loading?: boolean;
}

/**
 * 页面分区头部。
 */
export function SectionHeader({ title, description, actions, onRefresh, loading }: SectionHeaderProps): JSX.Element {
  return (
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-lg font-semibold tracking-normal">{title}</h2>
        {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions || onRefresh ? (
        <div className="flex flex-wrap gap-2">
          {actions}
          {onRefresh ? (
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
              <RefreshCcw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
              刷新
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export interface TooltipIconButtonProps extends Omit<ButtonProps, "children" | "size" | "aria-label"> {
  /**
   * 按钮提示文本。
   */
  label: string;
  /**
   * 按钮图标。
   */
  children: ReactNode;
}

/**
 * 带 Tooltip 的图标按钮。
 */
export function TooltipIconButton({ label, children, ...props }: TooltipIconButtonProps): JSX.Element {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button size="icon" aria-label={label} {...props}>
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

export interface ConfirmDialogProps {
  /**
   * 是否显示确认弹窗。
   */
  open: boolean;
  /**
   * 弹窗标题。
   */
  title: string;
  /**
   * 弹窗说明。
   */
  description: string;
  /**
   * 确认按钮文本。
   */
  confirmText?: string;
  /**
   * 确认按钮样式。
   */
  confirmVariant?: ButtonProps["variant"];
  /**
   * 是否处于提交中。
   */
  loading?: boolean;
  /**
   * 弹窗开关回调。
   */
  onOpenChange: (open: boolean) => void;
  /**
   * 确认回调。
   */
  onConfirm: () => void;
}

/**
 * 破坏性或高影响操作确认弹窗。
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmText = "确认",
  confirmVariant = "destructive",
  loading = false,
  onOpenChange,
  onConfirm,
}: ConfirmDialogProps): JSX.Element {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button type="button" variant={confirmVariant} loading={loading} onClick={onConfirm}>
            {confirmText}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * 标准字段标签。
 */
export function Field({ label, children, required, inline }: { label: string; children: ReactNode; required?: boolean; inline?: boolean }): JSX.Element {
  const [showError, setShowError] = useState(false);
  const isRequired = required ?? hasRequiredChild(children);
  const shouldShowError = isRequired && showError;
  const errorMessage = `${label}不能为空`;

  /**
   * 提交时捕获必填校验失败并显示自定义提示。
   */
  function handleInvalid(event: SyntheticEvent<HTMLElement>): void {
    if (!isRequired) return;
    if (!isEmptyRequiredControl(event.target)) return;
    event.preventDefault();
    setShowError(true);
  }

  /**
   * 输入有效值后清理当前字段提示。
   */
  function handleInput(event: SyntheticEvent<HTMLElement>): void {
    if (!showError) return;
    if (isEmptyRequiredControl(event.target)) return;
    setShowError(false);
  }

  return (
    <LabelPrimitive.Root className={inline ? "grid gap-1.5" : "grid gap-1.5"} onInvalidCapture={handleInvalid} onInputCapture={handleInput} onChangeCapture={handleInput}>
      <span className={inline ? "grid grid-cols-[auto_minmax(0,1fr)] items-center gap-2" : "grid gap-1.5"}>
        <span className="field-label whitespace-nowrap">
          {label}
          {isRequired ? <span className="ml-1 text-destructive">*</span> : null}
        </span>
        {children}
      </span>
      <span className={shouldShowError ? "min-h-4 text-xs leading-4 text-destructive" : "min-h-4 select-none text-xs leading-4 text-transparent"} aria-hidden={!shouldShowError}>
        {errorMessage}
      </span>
    </LabelPrimitive.Root>
  );
}

/**
 * 判断字段内容是否包含必填表单控件。
 */
function hasRequiredChild(children: ReactNode): boolean {
  return Children.toArray(children).some((child) => {
    if (!isValidElement<{ required?: boolean; children?: ReactNode }>(child)) return false;
    return Boolean(child.props.required) || hasRequiredChild(child.props.children);
  });
}

/**
 * 判断必填控件是否为空。
 */
function isEmptyRequiredControl(target: EventTarget): boolean {
  if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) {
    return target.required && target.validity.valueMissing;
  }
  return false;
}
