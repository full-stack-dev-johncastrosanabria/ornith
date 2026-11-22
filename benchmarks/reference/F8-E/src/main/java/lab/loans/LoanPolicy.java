package lab.loans;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/**
 * Library lending policy.
 * <ul>
 *   <li>A loan is due {@link MemberType#loanDays()} days after it starts; a due date that falls on a Saturday or
 *       Sunday moves to the following Monday.</li>
 *   <li>Late fee: 0.25 for every day the book is returned after its due date (returning on the due date is free),
 *       capped at 10.00 per loan.</li>
 * </ul>
 */
public final class LoanPolicy {
    private static final BigDecimal DAILY_FEE = new BigDecimal("0.25");
    private static final BigDecimal MAX_FEE = new BigDecimal("10.00");

    public LocalDate dueDate(LocalDate start, MemberType type) {
        return nextBusinessDay(start.plusDays(type.loanDays()));
    }

    LocalDate nextBusinessDay(LocalDate day) {
        switch (day.getDayOfWeek()) {
            case SATURDAY:
                return day.plusDays(2);
            case SUNDAY:
                return day.plusDays(1);
            default:
                return day;
        }
    }

    public BigDecimal lateFee(LocalDate dueOn, LocalDate returnedOn) {
        if (!returnedOn.isAfter(dueOn)) {
            return BigDecimal.ZERO.setScale(2);
        }
        long days = ChronoUnit.DAYS.between(dueOn, returnedOn);
        return DAILY_FEE.multiply(BigDecimal.valueOf(days)).setScale(2).min(MAX_FEE);
    }
}
