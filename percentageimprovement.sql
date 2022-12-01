SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		<Chris Baker>
-- Create date: <20221201>
-- Description:	This query will calculate a percentage improvement in any two compareable values - E.g. query performance 
-- use Exec SP_percentage_improvement @original = 11000, @new = 5000
-- =============================================
create PROCEDURE SP_Percentage_Improvement
	-- Add the parameters for the stored procedure here

 
@original float,
@new float,
@perc float  = null

AS

BEGIN

	SET NOCOUNT ON;

set @perc =  (@original - @new) / @original * 100

Print @perc
END
GO
